# Diagnosis Agent
import ast

from app.models.state import CodeGuardState

from app.prompts.diagnosis_prompt import DIAGNOSIS_PROMPT
from app.tools.groq_tools import ask_groq


def _extract_function_source(file_path: str, function_name: str, line_number: int):
    try:
        with open(file_path, "r", encoding="utf-8") as source_file:
            source = source_file.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name and node.lineno == line_number:
                    return ast.get_source_segment(source, node)

        lines = source.splitlines()
        start = max(line_number - 6, 0)
        end = min(line_number + 24, len(lines))
        return "\n".join(lines[start:end])

    except Exception:
        return ""


def _build_repository_context(suspects):
    snippets = []

    for suspect in suspects[:5]:
        source = _extract_function_source(
            suspect["file"],
            suspect["function"],
            suspect["line"]
        )

        if not source:
            continue

        snippets.append(
            "File: {file}\nFunction: {function}\nLine: {line}\nScore: {score}\n```python\n{source}\n```".format(
                file=suspect["file"],
                function=suspect["function"],
                line=suspect["line"],
                score=suspect["score"],
                source=source[:2500]
            )
        )

    if not snippets:
        return "No source snippets were available."

    return "\n\n".join(snippets)[:12000]


def diagnosis_agent(state: CodeGuardState):

    suspects = state["suspects"]

    bug_report = state["bug_report"]

    error_log = state.get("error_log", "")

    repository_context = _build_repository_context(suspects)

    prompt = DIAGNOSIS_PROMPT.format(

        bug_report=bug_report,

        error_log=error_log,

        suspects=suspects,

        repository_context=repository_context

    )

    diagnosis = ask_groq(prompt)

    return {

        "diagnosis": diagnosis

    }
