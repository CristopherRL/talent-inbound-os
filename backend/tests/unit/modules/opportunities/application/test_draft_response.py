"""Unit tests for GenerateDraft and EditDraft use cases."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from talent_inbound.modules.opportunities.application.generate_draft import (
    GenerateDraft,
)
from talent_inbound.modules.opportunities.application.edit_draft import EditDraft
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)

# Patch targets — must match the module where the symbol is looked up at runtime.
_EDIT_DRAFT_SESSION = "talent_inbound.modules.opportunities.application.edit_draft.get_current_session"


def _make_opportunity(opp_id="opp-1", candidate_id="cand-1"):
    """Create a mock Opportunity with extracted data."""
    opp = MagicMock()
    opp.id = opp_id
    opp.candidate_id = candidate_id
    opp.company_name = "TestCo"
    opp.role_title = "Senior Engineer"
    opp.salary_range = "$100-130K"
    opp.tech_stack = ["Python", "FastAPI"]
    opp.work_model = "REMOTE"
    opp.recruiter_name = "Jane"
    opp.recruiter_company = "Recruiter Inc"
    opp.missing_fields = []
    return opp


class TestGenerateDraft:
    """Tests for the GenerateDraft use case."""

    async def test_rejects_invalid_response_type(self):
        repo = AsyncMock()
        uc = GenerateDraft(opportunity_repo=repo, model_router=None)

        with pytest.raises(ValueError, match="Invalid response_type"):
            await uc.execute("opp-1", "INVALID_TYPE")

        # Should not even attempt to load the opportunity
        repo.find_by_id.assert_not_called()

    async def test_raises_if_opportunity_not_found(self):
        repo = AsyncMock()
        repo.find_by_id.return_value = None
        uc = GenerateDraft(opportunity_repo=repo, model_router=None)

        with pytest.raises(OpportunityNotFoundError):
            await uc.execute("opp-missing", "EXPRESS_INTEREST")

    async def test_valid_response_types_accepted(self):
        """All three response types should pass validation and generate a draft."""
        repo = AsyncMock()
        repo.find_by_id.return_value = _make_opportunity()
        uc = GenerateDraft(opportunity_repo=repo, model_router=None)

        for rt in ("REQUEST_INFO", "EXPRESS_INTEREST", "DECLINE"):
            # The late imports inside execute() need patching at the source
            mock_session = AsyncMock()
            mock_model = MagicMock()
            mock_model.id = "draft-1"
            mock_model.response_type = rt
            mock_model.generated_content = "Draft text"
            mock_model.edited_content = None
            mock_model.is_final = False
            mock_model.created_at = "2026-01-01T00:00:00Z"

            with patch(
                "talent_inbound.shared.infrastructure.database.get_current_session",
                return_value=mock_session,
            ), patch(
                "talent_inbound.modules.opportunities.infrastructure.orm_models.DraftResponseModel",
                return_value=mock_model,
            ):
                mock_session.refresh = AsyncMock()
                result = await uc.execute("opp-1", rt)

            assert result["response_type"] == rt


class TestEditDraft:
    """Tests for the EditDraft use case."""

    async def test_updates_edited_content(self):
        uc = EditDraft()

        mock_draft = MagicMock()
        mock_draft.id = "draft-1"
        mock_draft.opportunity_id = "opp-1"
        mock_draft.response_type = "EXPRESS_INTEREST"
        mock_draft.generated_content = "Original text"
        mock_draft.edited_content = None
        mock_draft.is_final = False
        mock_draft.created_at = "2026-01-01T00:00:00Z"

        with patch(_EDIT_DRAFT_SESSION) as mock_session_fn:
            mock_session = AsyncMock()
            mock_session_fn.return_value = mock_session
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_draft
            mock_session.execute.return_value = mock_result
            mock_session.refresh = AsyncMock()

            result = await uc.execute("opp-1", "draft-1", edited_content="Edited text")

        assert mock_draft.edited_content == "Edited text"

    async def test_marks_as_final(self):
        uc = EditDraft()

        mock_draft = MagicMock()
        mock_draft.id = "draft-1"
        mock_draft.opportunity_id = "opp-1"
        mock_draft.response_type = "DECLINE"
        mock_draft.generated_content = "Original"
        mock_draft.edited_content = None
        mock_draft.is_final = False
        mock_draft.created_at = "2026-01-01T00:00:00Z"

        with patch(_EDIT_DRAFT_SESSION) as mock_session_fn:
            mock_session = AsyncMock()
            mock_session_fn.return_value = mock_session
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_draft
            mock_session.execute.return_value = mock_result
            mock_session.refresh = AsyncMock()

            result = await uc.execute("opp-1", "draft-1", is_final=True)

        assert mock_draft.is_final is True

    async def test_raises_if_draft_not_found(self):
        uc = EditDraft()

        with patch(_EDIT_DRAFT_SESSION) as mock_session_fn:
            mock_session = AsyncMock()
            mock_session_fn.return_value = mock_session
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            with pytest.raises(ValueError, match="Draft not found"):
                await uc.execute("opp-1", "draft-missing", edited_content="text")
