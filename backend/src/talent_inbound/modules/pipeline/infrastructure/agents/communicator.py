"""Communicator agent — generates context-aware draft responses.

Uses SMART-tier LLM when available, falls back to template-based drafts
for mock-first development and testing. Three response types:
REQUEST_INFO, EXPRESS_INTEREST, DECLINE.
"""

import time
from datetime import UTC, datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt


def _build_opportunity_context(extracted_data: dict) -> str:
    """Format extracted opportunity data for the prompt."""
    parts = []
    if extracted_data.get("company_name"):
        parts.append(f"Company: {extracted_data['company_name']}")
    if extracted_data.get("role_title"):
        parts.append(f"Role: {extracted_data['role_title']}")
    if extracted_data.get("salary_range"):
        parts.append(f"Salary: {extracted_data['salary_range']}")
    if extracted_data.get("tech_stack"):
        parts.append(f"Tech stack: {', '.join(extracted_data['tech_stack'])}")
    if extracted_data.get("work_model"):
        parts.append(f"Work model: {extracted_data['work_model']}")
    if extracted_data.get("recruiter_name"):
        parts.append(f"Recruiter: {extracted_data['recruiter_name']}")
    if extracted_data.get("recruiter_company"):
        parts.append(f"Recruiter company: {extracted_data['recruiter_company']}")
    return "\n".join(parts) if parts else "Limited opportunity data available"


def _build_profile_context(profile) -> str:
    """Format candidate profile for the prompt."""
    if not profile:
        return "No profile data available"
    parts = []
    if profile.display_name:
        parts.append(f"Name: {profile.display_name}")
    if profile.professional_title:
        parts.append(f"Title: {profile.professional_title}")
    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")
    return "\n".join(parts) if parts else "No profile data available"


def _mock_draft(
    response_type: str,
    extracted_data: dict,
    profile=None,
    additional_context: str | None = None,
) -> str:
    """Generate template-based draft for mock-first development."""
    company = extracted_data.get("company_name", "your company")
    role = extracted_data.get("role_title", "the role")
    stack = extracted_data.get("tech_stack", [])
    recruiter = extracted_data.get("recruiter_name", "")

    greeting = f"Hi {recruiter}," if recruiter else "Hi,"
    name = profile.display_name if profile and profile.display_name else ""
    sign_off = f"\nBest regards,\n{name}" if name else "\nBest regards"
    # additional_context is only used by the LLM path — mock templates can't adapt to it

    if response_type == "REQUEST_INFO":
        missing = extracted_data.get("missing_fields", [])
        missing_text = (
            ", ".join(missing)
            if missing
            else "salary range, team size, and project details"
        )
        return (
            f"{greeting}\n\n"
            f"Thank you for reaching out about the {role} position at {company}. "
            f"I'd be interested in learning more, but I'd appreciate some additional details "
            f"before we proceed.\n\n"
            f"Could you share information on the following: {missing_text}?\n\n"
            f"Looking forward to hearing from you."
            f"{sign_off}"
        )

    if response_type == "EXPRESS_INTEREST":
        stack_mention = ""
        if stack:
            overlap = stack[:3]
            stack_mention = f" My experience with {', '.join(overlap)} aligns well with what you're looking for."
        return (
            f"{greeting}\n\n"
            f"Thank you for reaching out about the {role} opportunity at {company}. "
            f"This sounds like an interesting position that aligns with my background.{stack_mention}\n\n"
            f"I'd be happy to schedule a call to discuss the role in more detail and learn "
            f"about the team and upcoming projects.\n\n"
            f"What times work best for you?"
            f"{sign_off}"
        )

    # DECLINE
    return (
        f"{greeting}\n\n"
        f"Thank you for considering me for the {role} position at {company}. "
        f"I appreciate you reaching out.\n\n"
        f"After reviewing the opportunity, I've decided to pass at this time. "
        f"However, I'd be open to exploring future opportunities that may be a better fit.\n\n"
        f"Wishing you the best in your search."
        f"{sign_off}"
    )


async def _llm_draft(
    model: BaseChatModel,
    response_type: str,
    extracted_data: dict,
    profile=None,
    additional_context: str | None = None,
) -> str:
    """Use LLM to generate a draft response."""
    prompt_template = load_prompt("communicator")
    prompt = prompt_template.format(
        response_type=response_type,
        opportunity_context=_build_opportunity_context(extracted_data),
        profile_context=_build_profile_context(profile),
    )
    user_msg = f"Generate a {response_type} draft response."
    if additional_context:
        user_msg += (
            f"\n\nAdditional instructions from the user "
            f"(incorporate naturally, do not change the response language): "
            f"{additional_context}"
        )
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_msg),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    return content if isinstance(content, str) else str(content)


def create_communicator_node(
    model: BaseChatModel | None = None,
    profile_repo=None,
    response_type: str = "EXPRESS_INTEREST",
):
    """Factory: returns a communicator node function.

    For the pipeline graph, this generates an EXPRESS_INTEREST draft by default.
    For on-demand generation, use the GenerateDraft use case instead.

    Args:
        model: Optional LLM for draft generation.
        profile_repo: Optional ProfileRepository to load candidate profile.
        response_type: Type of response to generate.
    """

    async def communicator_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        extracted = state.get("extracted_data", {})

        # Load candidate profile
        profile = None
        if profile_repo:
            candidate_id = state.get("candidate_id", "")
            if candidate_id:
                try:
                    profile = await profile_repo.find_by_candidate_id(candidate_id)
                except Exception:
                    pass

        # Generate draft
        if model is not None:
            draft_text = await _llm_draft(model, response_type, extracted, profile)
            source = "llm"
        else:
            draft_text = _mock_draft(response_type, extracted, profile)
            source = "template"

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        log_entry: StepLog = {
            "step": "communicator",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(UTC).isoformat(),
            "detail": f"Draft generated ({response_type}) via {source}",
        }

        return {
            "draft_response": draft_text,
            "current_step": "communicator",
            "pipeline_log": [log_entry],
        }

    return communicator_node


async def generate_draft_standalone(
    response_type: str,
    extracted_data: dict,
    profile=None,
    model: BaseChatModel | None = None,
    additional_context: str | None = None,
) -> str:
    """Generate a draft response outside of the pipeline graph.

    Used by the GenerateDraft use case for on-demand generation.
    """
    if model is not None:
        return await _llm_draft(
            model, response_type, extracted_data, profile, additional_context
        )
    return _mock_draft(response_type, extracted_data, profile, additional_context)
