"""ExtractCVSkills use case — uses LLM to extract a skill list from CV text."""

import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter
from talent_inbound.modules.profile.domain.exceptions import ProfileNotFoundError
from talent_inbound.modules.profile.domain.repositories import ProfileRepository

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a technical recruiter assistant. Extract all technical and professional "
    "skills from the provided CV/resume text. Return ONLY a JSON array of skill "
    'strings, no markdown, no explanation. Example: ["Python", "FastAPI", "Docker"]. '
    "Include: programming languages, frameworks, databases, tools, cloud platforms, "
    "methodologies (e.g., Agile, TDD), and soft skills (e.g., Leadership). "
    "Normalize skill names to their canonical form (e.g., 'python' -> 'Python'). "
    "Return at most 50 skills. If no skills are found, return an empty array []."
)


def _parse_skill_list(raw: str) -> list[str]:
    """Parse JSON array from LLM output, handling markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        first_nl = text.index("\n") if "\n" in text else 3
        text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [s for s in parsed if isinstance(s, str) and s.strip()]
    except (json.JSONDecodeError, ValueError):
        pass
    return []


class ExtractCVSkills:
    """Extracts a skill list from the candidate's uploaded CV text via LLM."""

    def __init__(
        self,
        profile_repo: ProfileRepository,
        model_router: ModelRouter,
    ) -> None:
        self._profile_repo = profile_repo
        self._model_router = model_router

    async def execute(self, candidate_id: str) -> list[str]:
        profile = await self._profile_repo.find_by_candidate_id(candidate_id)
        if not profile:
            raise ProfileNotFoundError(candidate_id)

        if not profile.cv_extracted_text:
            return []

        model = self._model_router.get_model("extractor")
        if model is None:
            logger.warning("cv_skills_no_llm_configured", candidate_id=candidate_id)
            return []

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=profile.cv_extracted_text[:20000]),
        ]

        try:
            response = await model.ainvoke(messages)
            content = response.content
            if isinstance(content, list):
                content = " ".join(
                    b["text"]
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            skills = _parse_skill_list(str(content))
            logger.info(
                "cv_skills_extracted", count=len(skills), candidate_id=candidate_id
            )
            return skills
        except Exception:
            logger.exception("cv_skills_extraction_failed", candidate_id=candidate_id)
            return []
