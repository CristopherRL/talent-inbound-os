"""Analyst agent — scores opportunities against the candidate's profile.

Uses SMART-tier LLM when available, falls back to rule-based heuristic
for mock-first development and testing. Skips scoring when critical
fields are missing (INCOMPLETE_INFO).
"""

import json
import time
from datetime import datetime, timezone

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt


def _build_profile_context(profile) -> str:
    """Format candidate profile into a readable context string."""
    parts = []
    if profile.display_name:
        parts.append(f"Name: {profile.display_name}")
    if profile.professional_title:
        parts.append(f"Title: {profile.professional_title}")
    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")
    if profile.min_salary:
        currency = profile.preferred_currency or "USD"
        parts.append(f"Minimum salary: {profile.min_salary} {currency}")
    if profile.work_model:
        wm = profile.work_model.value if hasattr(profile.work_model, "value") else profile.work_model
        parts.append(f"Work model preference: {wm}")
    if profile.preferred_locations:
        parts.append(f"Locations: {', '.join(profile.preferred_locations)}")
    if profile.industries:
        parts.append(f"Industries: {', '.join(profile.industries)}")
    if profile.cv_extracted_text:
        cv_snippet = profile.cv_extracted_text[:500]
        parts.append(f"CV summary: {cv_snippet}")
    return "\n".join(parts) if parts else "No profile data available"


def _build_opportunity_context(extracted_data: dict) -> str:
    """Format extracted opportunity data into a readable context string."""
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
    if extracted_data.get("recruiter_type"):
        parts.append(f"Recruiter type: {extracted_data['recruiter_type']}")
    return "\n".join(parts) if parts else "No opportunity data available"


def _mock_score(profile, extracted_data: dict, weights: dict) -> dict:
    """Rule-based scoring heuristic for mock-first development.

    Weights are injected from config (Settings), not hardcoded.
    """
    score = weights["base"]
    reasoning_parts = []
    skill_matches = []
    missing_skills = []

    # Skills overlap
    if profile and profile.skills and extracted_data.get("tech_stack"):
        candidate_skills = {s.lower() for s in profile.skills}
        required_skills = {s.lower() for s in extracted_data["tech_stack"]}
        matched = candidate_skills & required_skills
        skill_matches = [s for s in extracted_data["tech_stack"] if s.lower() in matched]
        missing_skills = [s for s in extracted_data["tech_stack"] if s.lower() not in matched]

        if required_skills:
            overlap_ratio = len(matched) / len(required_skills)
            score += int(overlap_ratio * weights["skills"])
            reasoning_parts.append(
                f"Skills: {len(matched)}/{len(required_skills)} match ({overlap_ratio:.0%})"
            )

    # Work model match
    if profile and profile.work_model and extracted_data.get("work_model"):
        pref = profile.work_model.value if hasattr(profile.work_model, "value") else profile.work_model
        if pref == extracted_data["work_model"]:
            score += weights["wm_match"]
            reasoning_parts.append(f"Work model: {pref} matches")
        else:
            score += weights["wm_mismatch"]
            reasoning_parts.append(
                f"Work model: prefers {pref}, offer is {extracted_data['work_model']}"
            )

    # Salary delta
    salary_delta = "not specified"
    if profile and profile.min_salary and extracted_data.get("salary_range"):
        try:
            import re
            numbers = re.findall(r"\d[\d,]*", extracted_data["salary_range"])
            if numbers:
                max_offered = int(numbers[-1].replace(",", ""))
                if max_offered < 1000:
                    max_offered *= 1000
                diff = max_offered - profile.min_salary
                if diff >= 0:
                    score += weights["sal_meets"]
                    salary_delta = f"+{diff:,} above minimum"
                    reasoning_parts.append(f"Salary: meets minimum (+{diff:,})")
                else:
                    score += weights["sal_below"]
                    salary_delta = f"{diff:,} below minimum"
                    reasoning_parts.append(f"Salary: below minimum ({diff:,})")
        except (ValueError, IndexError):
            pass

    score = max(0, min(100, score))
    reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Base score with limited data"

    return {
        "score": score,
        "reasoning": reasoning,
        "skill_matches": skill_matches,
        "missing_skills": missing_skills,
        "salary_delta": salary_delta,
    }


async def _llm_score(model: BaseChatModel, profile, extracted_data: dict) -> dict:
    """Use LLM to score the opportunity against the profile."""
    prompt_template = load_prompt("analyst")
    prompt = prompt_template.format(
        profile_context=_build_profile_context(profile),
        opportunity_context=_build_opportunity_context(extracted_data),
    )
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content="Score this opportunity."),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    if isinstance(content, str):
        parsed = json.loads(content)
        return {
            "score": max(0, min(100, int(parsed.get("score", 50)))),
            "reasoning": parsed.get("reasoning", ""),
            "skill_matches": parsed.get("skill_matches", []),
            "missing_skills": parsed.get("missing_skills", []),
            "salary_delta": parsed.get("salary_delta", "not specified"),
        }
    return _mock_score(profile, extracted_data)


def _default_weights() -> dict:
    """Fallback weights when config is not injected (e.g., tests)."""
    return {
        "base": 50,
        "skills": 30,
        "wm_match": 10,
        "wm_mismatch": -5,
        "sal_meets": 10,
        "sal_below": -10,
    }


def create_analyst_node(
    model: BaseChatModel | None = None,
    profile_repo=None,
    scoring_weights: dict | None = None,
):
    """Factory: returns an analyst node function with optional LLM model.

    Args:
        model: Optional LLM for scoring reasoning.
        profile_repo: ProfileRepository to load the candidate's profile.
        scoring_weights: Dict with scoring weight values from config.
    """
    weights = scoring_weights or _default_weights()

    async def analyst_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        extracted = state.get("extracted_data", {})
        missing = extracted.get("missing_fields", [])

        # Skip scoring if critical fields are missing
        if missing:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            log_entry: StepLog = {
                "step": "analyst",
                "status": "skipped",
                "latency_ms": elapsed_ms,
                "tokens": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detail": f"Skipped: missing critical fields {missing}",
            }
            return {
                "match_score": None,
                "match_reasoning": None,
                "current_step": "analyst",
                "pipeline_log": [log_entry],
            }

        # Load candidate profile
        profile = None
        if profile_repo:
            candidate_id = state.get("candidate_id", "")
            if candidate_id:
                try:
                    profile = await profile_repo.find_by_candidate_id(candidate_id)
                except Exception:
                    pass

        # Score
        if model is not None and profile:
            result = await _llm_score(model, profile, extracted)
            source = "llm"
        else:
            result = _mock_score(profile, extracted, weights)
            source = "heuristic"

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        log_entry: StepLog = {
            "step": "analyst",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": f"Score: {result['score']}/100 via {source}. {result['reasoning']}",
        }

        return {
            "match_score": result["score"],
            "match_reasoning": result["reasoning"],
            "current_step": "analyst",
            "pipeline_log": [log_entry],
        }

    return analyst_node
