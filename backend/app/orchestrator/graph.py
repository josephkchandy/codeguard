from langgraph.graph import END, StateGraph

from app.models.state import CodeGuardState

from app.agents.scanner_agent import scanner_agent
from app.agents.bug_hunter_agent import bug_hunter_agent
from app.agents.diagnosis_agent import diagnosis_agent


def build_graph():

    builder = StateGraph(CodeGuardState)

    builder.add_node(
        "scanner",
        scanner_agent
    )

    builder.add_node(
        "bug_hunter",
        bug_hunter_agent
    )

    builder.add_node(
        "diagnosis",
        diagnosis_agent
    )

    builder.set_entry_point("scanner")

    builder.add_edge(
        "scanner",
        "bug_hunter"
    )

    builder.add_edge(
        "bug_hunter",
        "diagnosis"
    )

    builder.add_edge(
        "diagnosis",
        END
    )

    return builder.compile()


codeguard_graph = build_graph()