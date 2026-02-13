"""LangGraph StateGraph definitions for the processing pipeline.

Main pipeline: guardrail → gatekeeper → (conditional: spam→END, offer→extractor) → END
Analyst and Communicator are stubs — implemented in US5 and US7.
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.agents.extractor import (
    create_extractor_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.gatekeeper import (
    create_gatekeeper_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.guardrail import (
    guardrail_node,
)
from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter


def _route_after_gatekeeper(state: PipelineState) -> Literal["extractor", "__end__"]:
    """Conditional edge: skip extraction for spam/non-offers."""
    classification = state.get("classification", "")
    if classification == "REAL_OFFER":
        return "extractor"
    return "__end__"


def build_main_pipeline(model_router: ModelRouter | None = None) -> StateGraph:
    """Build and compile the main processing pipeline graph.

    Args:
        model_router: Optional ModelRouter for LLM-powered agents.
                      If None, agents use mock/heuristic fallbacks.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    gatekeeper_model = model_router.get_model("gatekeeper") if model_router else None
    extractor_model = model_router.get_model("extractor") if model_router else None

    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("gatekeeper", create_gatekeeper_node(gatekeeper_model))
    graph.add_node("extractor", create_extractor_node(extractor_model))

    # Edges: linear flow with conditional branch after gatekeeper
    graph.add_edge(START, "guardrail")
    graph.add_edge("guardrail", "gatekeeper")
    graph.add_conditional_edges(
        "gatekeeper",
        _route_after_gatekeeper,
        {"extractor": "extractor", "__end__": END},
    )
    graph.add_edge("extractor", END)

    return graph.compile()
