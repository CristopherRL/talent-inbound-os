"""LangGraph StateGraph definitions for the processing pipeline.

Main pipeline: guardrail → (injection→END | ok→gatekeeper)
  → gatekeeper → (spam→END | offer→extractor)
  → extractor → language_detector → (missing→END | ok→analyst)
  → analyst → communicator → stage_detector → END
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.agents.analyst import (
    create_analyst_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.communicator import (
    create_communicator_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.extractor import (
    create_extractor_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.gatekeeper import (
    create_gatekeeper_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.guardrail import (
    create_guardrail_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.language_detector import (
    create_language_detector_node,
)
from talent_inbound.modules.pipeline.infrastructure.agents.stage_detector import (
    create_stage_detector_node,
)
from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter


def _route_after_guardrail(
    state: PipelineState,
) -> Literal["gatekeeper", "__end__"]:
    """Conditional edge: stop pipeline if prompt injection was detected."""
    if state.get("prompt_injection_detected"):
        return "__end__"
    return "gatekeeper"


def _route_after_guardrail_followup(
    state: PipelineState,
) -> Literal["extractor", "__end__"]:
    """Conditional edge for follow-up pipeline (no gatekeeper)."""
    if state.get("prompt_injection_detected"):
        return "__end__"
    return "extractor"


def _route_after_gatekeeper(state: PipelineState) -> Literal["extractor", "__end__"]:
    """Conditional edge: skip extraction for spam/non-offers."""
    classification = state.get("classification", "")
    if classification == "REAL_OFFER":
        return "extractor"
    return "__end__"


def _route_after_language_detector(
    state: PipelineState,
) -> Literal["analyst", "__end__"]:
    """Conditional edge: skip scoring/drafting if critical fields are missing.

    NOTE: Language detection always runs (even for incomplete offers) so that
    on-demand draft generation can match the recruiter's language.
    """
    extracted = state.get("extracted_data", {})
    missing = extracted.get("missing_fields", [])
    if missing:
        return "__end__"
    return "analyst"


def build_main_pipeline(
    model_router: ModelRouter | None = None,
    profile_repo=None,
    scoring_weights: dict | None = None,
    opportunity_repo=None,
) -> StateGraph:
    """Build and compile the main processing pipeline graph.

    Args:
        model_router: Optional ModelRouter for LLM-powered agents.
        profile_repo: Optional ProfileRepository for Analyst to load candidate profile.
        scoring_weights: Optional dict with scoring weight values from config.
        opportunity_repo: Optional OpportunityRepository for Stage Detector.

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    guardrail_model = model_router.get_model("guardrail") if model_router else None
    gatekeeper_model = model_router.get_model("gatekeeper") if model_router else None
    extractor_model = model_router.get_model("extractor") if model_router else None
    language_detector_model = (
        model_router.get_model("language_detector") if model_router else None
    )
    analyst_model = model_router.get_model("analyst") if model_router else None
    communicator_model = (
        model_router.get_model("communicator") if model_router else None
    )
    stage_detector_model = (
        model_router.get_model("stage_detector") if model_router else None
    )

    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("guardrail", create_guardrail_node(guardrail_model))
    graph.add_node("gatekeeper", create_gatekeeper_node(gatekeeper_model))
    graph.add_node("extractor", create_extractor_node(extractor_model))
    graph.add_node(
        "language_detector", create_language_detector_node(language_detector_model)
    )
    graph.add_node(
        "analyst",
        create_analyst_node(
            model=analyst_model,
            profile_repo=profile_repo,
            scoring_weights=scoring_weights,
        ),
    )
    graph.add_node(
        "communicator",
        create_communicator_node(
            model=communicator_model,
            profile_repo=profile_repo,
        ),
    )
    graph.add_node(
        "stage_detector",
        create_stage_detector_node(
            model=stage_detector_model,
            opportunity_repo=opportunity_repo,
        ),
    )

    # Edges
    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges(
        "guardrail",
        _route_after_guardrail,
        {"gatekeeper": "gatekeeper", "__end__": END},
    )
    graph.add_conditional_edges(
        "gatekeeper",
        _route_after_gatekeeper,
        {"extractor": "extractor", "__end__": END},
    )
    graph.add_edge("extractor", "language_detector")
    graph.add_conditional_edges(
        "language_detector",
        _route_after_language_detector,
        {"analyst": "analyst", "__end__": END},
    )
    graph.add_edge("analyst", "communicator")
    graph.add_edge("communicator", "stage_detector")
    graph.add_edge("stage_detector", END)

    return graph.compile()


def build_followup_pipeline(
    model_router: ModelRouter | None = None,
    profile_repo=None,
    scoring_weights: dict | None = None,
    opportunity_repo=None,
) -> StateGraph:
    """Build the follow-up pipeline — same as main but skips Gatekeeper.

    We already know this is a real offer (it was classified during initial ingestion),
    guardrail → extractor → language_detector → analyst → communicator → stage_detector.
    """
    guardrail_model = model_router.get_model("guardrail") if model_router else None
    extractor_model = model_router.get_model("extractor") if model_router else None
    language_detector_model = (
        model_router.get_model("language_detector") if model_router else None
    )
    analyst_model = model_router.get_model("analyst") if model_router else None
    communicator_model = (
        model_router.get_model("communicator") if model_router else None
    )
    stage_detector_model = (
        model_router.get_model("stage_detector") if model_router else None
    )

    graph = StateGraph(PipelineState)

    # Nodes — no gatekeeper
    graph.add_node("guardrail", create_guardrail_node(guardrail_model))
    graph.add_node("extractor", create_extractor_node(extractor_model))
    graph.add_node(
        "language_detector", create_language_detector_node(language_detector_model)
    )
    graph.add_node(
        "analyst",
        create_analyst_node(
            model=analyst_model,
            profile_repo=profile_repo,
            scoring_weights=scoring_weights,
        ),
    )
    graph.add_node(
        "communicator",
        create_communicator_node(
            model=communicator_model,
            profile_repo=profile_repo,
        ),
    )
    graph.add_node(
        "stage_detector",
        create_stage_detector_node(
            model=stage_detector_model,
            opportunity_repo=opportunity_repo,
        ),
    )

    # Edges: guardrail → (injection→END | ok→extractor) → ...
    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges(
        "guardrail",
        _route_after_guardrail_followup,
        {"extractor": "extractor", "__end__": END},
    )
    graph.add_edge("extractor", "language_detector")
    graph.add_conditional_edges(
        "language_detector",
        _route_after_language_detector,
        {"analyst": "analyst", "__end__": END},
    )
    graph.add_edge("analyst", "communicator")
    graph.add_edge("communicator", "stage_detector")
    graph.add_edge("stage_detector", END)

    return graph.compile()
