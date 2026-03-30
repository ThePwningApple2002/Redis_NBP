from langgraph.graph import END, START, StateGraph

from app.graph.nodes import generate, retrieve
from app.graph.state import GraphState

_graph = None


def build_graph():
    global _graph
    if _graph is not None:
        return _graph

    builder = StateGraph(GraphState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    _graph = builder.compile()
    return _graph
