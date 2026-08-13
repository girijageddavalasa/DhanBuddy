from pathlib import Path
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from memory import DEFAULT_DATABASE_PATH, forget_me, lookup_user, save_user_memory


class MemoryState(TypedDict, total=False):
    user_id: str
    user_name: str | None
    preferred_language: str | None
    memory_consent: bool
    new_fact_key: str
    new_fact_value: str
    memory_lookup_result: dict[str, object] | None
    action: Literal["lookup", "save", "forget", "continue"]
    response_context: str
    database_path: str
    operation_succeeded: bool


def _database_path(state: MemoryState) -> Path:
    return Path(state.get("database_path", str(DEFAULT_DATABASE_PATH)))


def lookup_node(state: MemoryState) -> MemoryState:
    memory = lookup_user(state["user_id"], _database_path(state))
    if memory is None:
        return {
            "memory_lookup_result": None,
            "response_context": "No saved memory exists for this user.",
            "operation_succeeded": True,
        }
    context = f"Returning user: {memory.name}." if memory.name else "Returning user."
    return {
        "user_name": memory.name,
        "preferred_language": memory.preferred_language,
        "memory_consent": memory.memory_consent,
        "memory_lookup_result": {
            "name": memory.name,
            "preferred_language": memory.preferred_language,
            "facts": memory.facts,
        },
        "response_context": context,
        "operation_succeeded": True,
    }


def request_consent_node(state: MemoryState) -> MemoryState:
    if not state.get("memory_consent", False):
        return {
            "response_context": "Ask the user for permission before saving.",
            "operation_succeeded": False,
        }
    return {}


def save_node(state: MemoryState) -> MemoryState:
    memory = save_user_memory(
        state["user_id"], state["new_fact_key"], state["new_fact_value"], True,
        _database_path(state),
    )
    return {
        "memory_lookup_result": {"facts": memory.facts},
        "response_context": "The approved memory was saved.",
        "operation_succeeded": True,
    }


def discard_node(state: MemoryState) -> MemoryState:
    return {
        "response_context": "The information was not saved.",
        "operation_succeeded": False,
    }


def forget_node(state: MemoryState) -> MemoryState:
    deleted = forget_me(state["user_id"], _database_path(state))
    return {
        "memory_lookup_result": None,
        "response_context": "Stored memory was deleted." if deleted else "No memory existed.",
        "operation_succeeded": deleted,
    }


def route_action(state: MemoryState) -> str:
    return state.get("action", "continue")


def route_consent(state: MemoryState) -> str:
    return "save" if state.get("memory_consent", False) else "discard"


def build_memory_graph():
    graph = StateGraph(MemoryState)
    graph.add_node("lookup", lookup_node)
    graph.add_node("request_consent", request_consent_node)
    graph.add_node("save", save_node)
    graph.add_node("discard", discard_node)
    graph.add_node("forget", forget_node)
    graph.add_conditional_edges(
        START, route_action,
        {"lookup": "lookup", "save": "request_consent", "forget": "forget", "continue": END},
    )
    graph.add_conditional_edges(
        "request_consent", route_consent, {"save": "save", "discard": "discard"}
    )
    for node in ("lookup", "save", "discard", "forget"):
        graph.add_edge(node, END)
    return graph.compile()


memory_graph = build_memory_graph()


def run_memory_workflow(state: MemoryState) -> MemoryState:
    return memory_graph.invoke(state)
