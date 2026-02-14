"""Opportunity domain entity for the opportunities module."""

from datetime import datetime, timezone

from pydantic import Field

from talent_inbound.shared.domain.base_entity import AggregateRoot, Entity, _utcnow
from talent_inbound.shared.domain.enums import (
    OpportunityStatus,
    RecruiterType,
    STANDARD_FLOW,
    TERMINAL_STATUSES,
    TransitionTrigger,
    WorkModel,
)


class StatusTransition(Entity):
    """Audit log entry for a status change on an Opportunity."""

    opportunity_id: str
    from_status: OpportunityStatus
    to_status: OpportunityStatus
    triggered_by: TransitionTrigger
    is_unusual: bool = False
    note: str | None = None


class Opportunity(AggregateRoot):
    """The structured, evaluated vacancy. Core aggregate for tracking."""

    candidate_id: str
    company_name: str | None = None
    client_name: str | None = None
    role_title: str | None = None
    salary_range: str | None = None
    tech_stack: list[str] = []
    work_model: WorkModel | None = None
    recruiter_name: str | None = None
    recruiter_type: RecruiterType | None = None
    recruiter_company: str | None = None
    match_score: int | None = None
    match_reasoning: str | None = None
    missing_fields: list[str] = []
    status: OpportunityStatus = OpportunityStatus.NEW
    is_archived: bool = False
    last_interaction_at: datetime = Field(default_factory=_utcnow)

    def change_status(
        self,
        new_status: OpportunityStatus,
        triggered_by: TransitionTrigger,
        note: str | None = None,
    ) -> StatusTransition:
        """Transition to a new status and return the audit record.

        Detects unusual transitions (skipping stages, backward movement,
        moving from terminal states).
        """
        is_unusual = self._is_unusual_transition(new_status)
        transition = StatusTransition(
            opportunity_id=self.id,
            from_status=self.status,
            to_status=new_status,
            triggered_by=triggered_by,
            is_unusual=is_unusual,
            note=note,
        )
        self.status = new_status
        self.touch()
        return transition

    def _is_unusual_transition(self, new_status: OpportunityStatus) -> bool:
        """Check if the transition is unusual (skip, backward, or from terminal).

        Rules:
        - Moving FROM a terminal status is always unusual.
        - Within STANDARD_FLOW: backward or skipping >1 stage is unusual.
        - Going to OFFER without reaching INTERVIEWING first is unusual
          (skipping stages toward a positive outcome).
        """
        if self.status in TERMINAL_STATUSES:
            return True

        if self.status in STANDARD_FLOW and new_status in STANDARD_FLOW:
            from_idx = STANDARD_FLOW.index(self.status)
            to_idx = STANDARD_FLOW.index(new_status)
            if to_idx < from_idx:
                return True
            if to_idx - from_idx > 1:
                return True

        # OFFER should follow INTERVIEWING — skipping to it is unusual
        if new_status == OpportunityStatus.OFFER and self.status in STANDARD_FLOW:
            if self.status != OpportunityStatus.INTERVIEWING:
                return True

        return False

    def record_interaction(self) -> None:
        """Update last_interaction_at timestamp."""
        self.last_interaction_at = datetime.now(timezone.utc)
        self.touch()
