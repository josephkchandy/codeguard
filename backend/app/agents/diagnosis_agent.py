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
        repository_context = self.build_repository_context(suspects)
        fallback = self.build_fallback_response(suspects)

        prompt = DIAGNOSIS_PROMPT.format(
            bug_report=state["bug_report"],
            error_log=state.get("error_log", ""),
            suspects=suspects,
            repository_context=repository_context
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
                }
            ]
        }

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
