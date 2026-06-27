# Bug Hunter Agent
from app.models.state import CodeGuardState
from app.tools.bug_tools import BugTools


def bug_hunter_agent(state: CodeGuardState):

    keywords = BugTools.tokenize(state["bug_report"])

    suspects = []
    fallback = []

    repository = state["repository_map"]

    for file_name, details in repository.items():

        file_lower = file_name.lower()

        for function in details["functions"]:

            score = 0

            name = function["name"].lower()
            docstring = (function.get("docstring") or "").lower()

            for keyword in keywords:

                if keyword in name:
                    score += 2

                if keyword in file_lower:
                    score += 1

                if keyword in docstring:
                    score += 1

            candidate = {

                "file": file_name,

                "function": function["name"],

                "line": function["line"],

                "score": score

            }

            if score > 0:

                suspects.append(candidate)

            elif len(fallback) < 5:
                fallback.append(candidate)

    suspects.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    return {

        "suspects": suspects[:5] if suspects else fallback

    }
