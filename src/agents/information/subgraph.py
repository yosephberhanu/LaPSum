from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.utils import State
from .supervisor import information_supervisor_node
from .source_code import information_source_code_node
from .git import information_git_node
from .github import information_github_node
from .docs import information_docs_node

MAX_INFORMATION_ROUNDS = 3  # Limit on sequential calls


def call_next_agent(state: State) -> str:
    if state.get("rounds", 0) >= MAX_INFORMATION_ROUNDS:
        return "end"

    agent_fields = {
        "source_code": ("source_query", "source_response"),
        "git": ("git_query", "git_response"),
        "github": ("github_query", "github_response"),
        "docs": ("docs_query", "docs_response"),
    }

    for agent, (query_field, response_field) in agent_fields.items():
        query = state.get(query_field)
        response = state.get(response_field)

        if (
            query != "PASS"
            and query not in [None, [], ""]
            and (not response or response in [[], "", None])
        ):
            return f"information_{agent}"

    return "end"

def create_information_subgraph():
    workflow = StateGraph(State)

    workflow.add_node("information_supervisor", information_supervisor_node)
    workflow.add_node("information_source_code", information_source_code_node)
    workflow.add_node("information_git", information_git_node)
    workflow.add_node("information_github", information_github_node)
    workflow.add_node("information_docs", information_docs_node)

    workflow.add_edge(START, "information_supervisor")
    workflow.add_conditional_edges(
        "information_supervisor",
        call_next_agent,
        {
            "information_source_code": "information_source_code",
            "information_git": "information_git",
            "information_github": "information_github",
            "information_docs": "information_docs",
            "end": END
        }
    )

    # 👇 Fix: define each increment_round as a named function
    def increment_after_source(state: State):
        state["rounds"] = state.get("rounds", 0) + 1
        return state

    def increment_after_git(state: State):
        state["rounds"] = state.get("rounds", 0) + 1
        return state

    def increment_after_github(state: State):
        state["rounds"] = state.get("rounds", 0) + 1
        return state

    def increment_after_docs(state: State):
        state["rounds"] = state.get("rounds", 0) + 1
        return state

    workflow.add_node("rounds_information_source_code", increment_after_source)
    workflow.add_edge("information_source_code", "rounds_information_source_code")
    workflow.add_edge("rounds_information_source_code", "information_supervisor")

    workflow.add_node("rounds_information_git", increment_after_git)
    workflow.add_edge("information_git", "rounds_information_git")
    workflow.add_edge("rounds_information_git", "information_supervisor")

    workflow.add_node("rounds_information_github", increment_after_github)
    workflow.add_edge("information_github", "rounds_information_github")
    workflow.add_edge("rounds_information_github", "information_supervisor")

    workflow.add_node("rounds_information_docs", increment_after_docs)
    workflow.add_edge("information_docs", "rounds_information_docs")
    workflow.add_edge("rounds_information_docs", "information_supervisor")

    return workflow.compile()