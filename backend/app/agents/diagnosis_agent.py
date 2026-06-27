import json

from app.models.state import CodeGuardState
from app.prompts.diagnosis_prompt import DIAGNOSIS_PROMPT
from app.tools.groq_tools import ask_groq
from app.tools.source_tools import SourceTools


class DiagnosisAgent:
    role = "LLM-backed root-cause and repair agent"
    goal = "Explain the bug and propose corrected code using ranked evidence."
    tools = [
        "source snippet extractor",
        "bug hunter triage evidence",
        "error log context",
        "Groq/LangChain reasoning model",
    ]

    def __call__(self, state: CodeGuardState):
        return self.run(state)

    def run(self, state: CodeGuardState):
        suspects = state["suspects"]
        actions = self.plan_actions(state, suspects)
        observations = self.execute_actions(actions, suspects)
        repository_context = self.build_repository_context(suspects)
        fallback = self.build_fallback_response(suspects)

        prompt = DIAGNOSIS_PROMPT.format(
            bug_report=state["bug_report"],
            error_log=state.get("error_log", ""),
            suspects=suspects,
            repository_context=repository_context,
            agent_observations=json.dumps(observations, indent=2)
        )

        diagnosis = ask_groq(prompt, fallback=fallback)
        diagnosis = self.normalize_diagnosis(diagnosis, fallback)

        return {
            "diagnosis": diagnosis,
            "agent_reports": [
                *state.get("agent_reports", []),
                {
                    "agent": "diagnosis",
                    "role": self.role,
                    "goal": self.goal,
                    "tools": self.tools,
                    "summary": diagnosis.get("root_cause", "Diagnosis unavailable."),
                    "actions": actions,
                    "observations": observations,
                }
            ]
        }

    def plan_actions(self, state: CodeGuardState, suspects):
        fallback = {
            "thought": "Inspect the top suspect source and triage evidence before producing the repair.",
            "actions": [
                {
                    "tool": "inspect_suspect_source",
                    "file": suspect["file"],
                    "function": suspect["function"],
                    "line": suspect["line"],
                    "reason": "Top-ranked suspect from Bug Hunter Agent."
                }
                for suspect in suspects[:2]
            ]
        }

        prompt = """
You are CodeGuard's Diagnosis Agent.

Before writing the final diagnosis, choose tool actions.

Available tools:
- inspect_suspect_source: inspect a suspect function's source code.
- inspect_triage_reason: inspect why Bug Hunter ranked a suspect.

Bug Report:
{bug_report}

Error Log:
{error_log}

Suspects:
{suspects}

Return ONLY valid JSON:
{{
  "thought": "...",
  "actions": [
    {{
      "tool": "inspect_suspect_source | inspect_triage_reason",
      "file": "...",
      "function": "...",
      "line": 1,
      "reason": "..."
    }}
  ]
}}

Rules:
- Choose at most 4 actions.
- Only target suspects from the suspects list.
- Use source inspection when corrected code is expected.
""".format(
            bug_report=state.get("bug_report", ""),
            error_log=state.get("error_log", ""),
            suspects=json.dumps(suspects, indent=2)
        )

        plan = ask_groq(prompt, fallback=fallback)
        actions = plan.get("actions") if isinstance(plan, dict) else None

        if not isinstance(actions, list):
            return fallback["actions"]

        suspect_keys = {
            (suspect["file"], suspect["function"], suspect["line"])
            for suspect in suspects
        }
        valid_actions = []

        for action in actions[:4]:
            if not isinstance(action, dict):
                continue

            key = (
                action.get("file", ""),
                action.get("function", ""),
                int(action.get("line") or 0)
            )

            if action.get("tool") not in {"inspect_suspect_source", "inspect_triage_reason"}:
                continue

            if key not in suspect_keys:
                continue

            valid_actions.append({
                "tool": action["tool"],
                "file": key[0],
                "function": key[1],
                "line": key[2],
                "reason": action.get("reason", ""),
            })

        return valid_actions or fallback["actions"]

    def execute_actions(self, actions, suspects):
        suspect_index = {
            (suspect["file"], suspect["function"], suspect["line"]): suspect
            for suspect in suspects
        }
        observations = []

        for action in actions:
            key = (action["file"], action["function"], action["line"])
            suspect = suspect_index.get(key, {})

            if action["tool"] == "inspect_suspect_source":
                result = SourceTools.extract_function_source(
                    action["file"],
                    action["function"],
                    action["line"]
                )[:2600]
            else:
                result = {
                    "reason": suspect.get("reason", ""),
                    "signals": suspect.get("signals", []),
                    "score": suspect.get("score", 0),
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

    def build_repository_context(self, suspects):
        snippets = []

        for suspect in suspects[:5]:
            source = SourceTools.extract_function_source(
                suspect["file"],
                suspect["function"],
                suspect["line"]
            )

            if not source:
                continue

            snippets.append(
                "File: {file}\nFunction: {function}\nLine: {line}\nScore: {score}\nReason: {reason}\nSignals: {signals}\n```python\n{source}\n```".format(
                    file=suspect["file"],
                    function=suspect["function"],
                    line=suspect["line"],
                    score=suspect["score"],
                    reason=suspect.get("reason", ""),
                    signals=", ".join(suspect.get("signals", [])),
                    source=source[:2500]
                )
            )

        return "\n\n".join(snippets)[:12000] or "No source snippets were available."

    def build_fallback_response(self, suspects):
        primary = suspects[0] if suspects else {}

        return {
            "root_cause": "The diagnosis agent could not get a valid structured LLM response.",
            "suggested_fix": "Inspect the top-ranked suspect and rerun analysis with a more specific bug report or stack trace.",
            "target_file": primary.get("file", ""),
            "target_function": primary.get("function", ""),
            "corrected_code": "",
            "confidence": "Low"
        }

    def normalize_diagnosis(self, diagnosis, fallback):
        if not isinstance(diagnosis, dict):
            return fallback

        return {
            "root_cause": diagnosis.get("root_cause") or fallback["root_cause"],
            "suggested_fix": diagnosis.get("suggested_fix") or fallback["suggested_fix"],
            "target_file": diagnosis.get("target_file") or fallback["target_file"],
            "target_function": diagnosis.get("target_function") or fallback["target_function"],
            "corrected_code": diagnosis.get("corrected_code") or fallback["corrected_code"],
            "confidence": diagnosis.get("confidence") or fallback["confidence"],
        }


diagnosis = DiagnosisAgent()


def diagnosis_agent(state: CodeGuardState):
    return diagnosis(state)
