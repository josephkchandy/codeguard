import json
import re

from app.models.state import CodeGuardState
from app.prompts.bug_hunter_prompt import BUG_HUNTER_PROMPT
from app.tools.bug_tools import BugTools
from app.tools.groq_tools import ask_groq
from app.tools.source_tools import SourceTools


class BugHunterAgent:
    role = "LLM-backed debugging triage agent"
    goal = "Rank the functions most likely related to the submitted bug."
    tools = [
        "bug report tokenizer",
        "stack trace parser",
        "static candidate scorer",
        "source snippet extractor",
        "Groq/LangChain reasoning model",
    ]

    def __call__(self, state: CodeGuardState):
        return self.run(state)

    def run(self, state: CodeGuardState):
        candidates = self.collect_candidates(state)
        actions = self.plan_actions(state, candidates)
        observations = self.execute_actions(actions, candidates)
        source_context = self.build_source_context(candidates)
        fallback = self.build_fallback_response(candidates)

        prompt = BUG_HUNTER_PROMPT.format(
            bug_report=state["bug_report"],
            error_log=state.get("error_log", ""),
            candidates=json.dumps(candidates[:12], indent=2),
            source_context=source_context,
            agent_observations=json.dumps(observations, indent=2)
        )

        triage = ask_groq(prompt, fallback=fallback)
        suspects = self.normalize_suspects(triage, fallback)

        return {
            "suspects": suspects,
            "agent_reports": [
                *state.get("agent_reports", []),
                {
                    "agent": "bug_hunter",
                    "role": self.role,
                    "goal": self.goal,
                    "tools": self.tools,
                    "summary": triage.get("triage_summary", fallback["triage_summary"]),
                    "actions": actions,
                    "observations": observations,
                }
            ]
        }

    def plan_actions(self, state: CodeGuardState, candidates):
        fallback = {
            "thought": "Inspect the highest-ranked static candidates before final triage.",
            "actions": [
                {
                    "tool": "inspect_source",
                    "file": candidate["file"],
                    "function": candidate["function"],
                    "line": candidate["line"],
                    "reason": "Top static candidate."
                }
                for candidate in candidates[:3]
            ]
        }

        prompt = """
You are CodeGuard's Bug Hunter Agent.

Before final triage, choose which tools to use.

Available tools:
- inspect_source: inspect a candidate function's source code.
- inspect_static_signals: inspect static ranking signals for a candidate.

Bug Report:
{bug_report}

Error Log:
{error_log}

Candidates:
{candidates}

Return ONLY valid JSON:
{{
  "thought": "...",
  "actions": [
    {{
      "tool": "inspect_source | inspect_static_signals",
      "file": "...",
      "function": "...",
      "line": 1,
      "reason": "..."
    }}
  ]
}}

Rules:
- Choose at most 4 actions.
- Only choose tools from the available tools list.
- Only target files/functions from the candidates list.
""".format(
            bug_report=state.get("bug_report", ""),
            error_log=state.get("error_log", ""),
            candidates=json.dumps(candidates[:10], indent=2)
        )

        plan = ask_groq(prompt, fallback=fallback)
        actions = plan.get("actions") if isinstance(plan, dict) else None

        if not isinstance(actions, list):
            return fallback["actions"]

        valid_actions = []
        candidate_keys = {
            (candidate["file"], candidate["function"], candidate["line"])
            for candidate in candidates
        }

        for action in actions[:4]:
            if not isinstance(action, dict):
                continue

            key = (
                action.get("file", ""),
                action.get("function", ""),
                int(action.get("line") or 0)
            )

            if action.get("tool") not in {"inspect_source", "inspect_static_signals"}:
                continue

            if key not in candidate_keys:
                continue

            valid_actions.append({
                "tool": action["tool"],
                "file": key[0],
                "function": key[1],
                "line": key[2],
                "reason": action.get("reason", ""),
            })

        return valid_actions or fallback["actions"]

    def execute_actions(self, actions, candidates):
        candidate_index = {
            (candidate["file"], candidate["function"], candidate["line"]): candidate
            for candidate in candidates
        }
        observations = []

        for action in actions:
            key = (action["file"], action["function"], action["line"])
            candidate = candidate_index.get(key, {})

            if action["tool"] == "inspect_source":
                result = SourceTools.extract_function_source(
                    action["file"],
                    action["function"],
                    action["line"]
                )[:2200]
            else:
                result = {
                    "score": candidate.get("score", 0),
                    "signals": candidate.get("signals", []),
                    "static_reason": candidate.get("reason", ""),
                }

            observations.append({
                "tool": action["tool"],
                "target": {
                    "file": action["file"],
                    "function": action["function"],
                    "line": action["line"],
                },
                "reason": action.get("reason", ""),
                "result": result,
            })

        return observations

    def collect_candidates(self, state: CodeGuardState):
        keywords = BugTools.tokenize(
            " ".join([state.get("bug_report", ""), state.get("error_log", "")])
        )
        stack_trace_refs = self.extract_stack_trace_refs(state.get("error_log", ""))
        candidates = []

        for file_name, details in state["repository_map"].items():
            file_lower = file_name.lower()

            for function in details["functions"]:
                signals = []
                score = 0
                name = function["name"].lower()
                docstring = (function.get("docstring") or "").lower()

                for keyword in keywords:
                    if keyword in name:
                        score += 3
                        signals.append(f"keyword '{keyword}' appears in function name")

                    if keyword in file_lower:
                        score += 2
                        signals.append(f"keyword '{keyword}' appears in file path")

                    if keyword in docstring:
                        score += 1
                        signals.append(f"keyword '{keyword}' appears in docstring")

                for ref in stack_trace_refs:
                    if ref["file"].lower() in file_lower:
                        score += 4
                        signals.append(f"error log references {ref['file']}")

                    if ref["function"] and ref["function"].lower() == name:
                        score += 5
                        signals.append(f"stack trace references function {ref['function']}")

                candidates.append({
                    "file": file_name,
                    "function": function["name"],
                    "line": function["line"],
                    "score": min(score, 10),
                    "signals": sorted(set(signals))[:6],
                    "reason": self.build_static_reason(signals),
                })

        candidates.sort(key=lambda item: item["score"], reverse=True)

        if any(candidate["score"] > 0 for candidate in candidates):
            return candidates[:12]

        return candidates[:8]

    def build_source_context(self, candidates):
        snippets = []

        for candidate in candidates[:8]:
            source = SourceTools.extract_function_source(
                candidate["file"],
                candidate["function"],
                candidate["line"]
            )

            if not source:
                continue

            snippets.append(
                "File: {file}\nFunction: {function}\nLine: {line}\nStatic score: {score}\nSignals: {signals}\n```python\n{source}\n```".format(
                    file=candidate["file"],
                    function=candidate["function"],
                    line=candidate["line"],
                    score=candidate["score"],
                    signals=", ".join(candidate["signals"]) or "no direct static signal",
                    source=source[:1800]
                )
            )

        return "\n\n".join(snippets)[:12000] or "No source snippets were available."

    def build_fallback_response(self, candidates):
        suspects = []

        for candidate in candidates[:5]:
            score = candidate["score"] if candidate["score"] > 0 else 1
            suspects.append({
                **candidate,
                "score": score,
                "reason": candidate["reason"] or "Included as a fallback candidate from repository structure.",
            })

        return {
            "triage_summary": "Static triage fallback was used because the LLM response was unavailable or invalid.",
            "suspects": suspects,
        }

    def normalize_suspects(self, triage, fallback):
        raw_suspects = triage.get("suspects")

        if not isinstance(raw_suspects, list) or not raw_suspects:
            return fallback["suspects"]

        normalized = []

        for item in raw_suspects[:5]:
            if not isinstance(item, dict):
                continue

            normalized.append({
                "file": item.get("file", ""),
                "function": item.get("function", ""),
                "line": int(item.get("line") or 0),
                "score": int(item.get("score") or 1),
                "reason": item.get("reason", ""),
                "signals": item.get("signals", []),
            })

        return normalized or fallback["suspects"]

    def extract_stack_trace_refs(self, error_log):
        refs = []
        pattern = re.compile(r'File "([^"]+)", line \d+(?:, in ([\w_]+))?')

        for match in pattern.finditer(error_log or ""):
            refs.append({
                "file": match.group(1).replace("\\", "/").split("/")[-1],
                "function": match.group(2) or "",
            })

        return refs

    def build_static_reason(self, signals):
        if not signals:
            return ""

        return "Static evidence: " + "; ".join(sorted(set(signals))[:3]) + "."


bug_hunter = BugHunterAgent()


def bug_hunter_agent(state: CodeGuardState):
    return bug_hunter(state)
