"""Opportunity domain entity for the opportunities module."""

from datetime import UTC, datetime

from pydantic import Field

from talent_inbound.shared.domain.base_entity import AggregateRoot, Entity, _utcnow
from talent_inbound.shared.domain.enums import (
    STAGE_FLOW,
    TERMINAL_STAGES,
    OpportunityStage,
    RecruiterType,
    TransitionTrigger,
    WorkModel,
)


class StageTransition(Entity):
    """Audit log entry for a stage change on an Opportunity."""

    opportunity_id: str
    from_stage: OpportunityStage
    to_stage: OpportunityStage
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
    stage: OpportunityStage = OpportunityStage.DISCOVERY
    suggested_stage: OpportunityStage | None = None
    suggested_stage_reason: str | None = None
    is_archived: bool = False
    last_interaction_at: datetime = Field(default_factory=_utcnow)

    def change_stage(
        self,
        new_stage: OpportunityStage,
        triggered_by: TransitionTrigger,
        note: str | None = None,
    ) -> StageTransition:
        """Transition to a new stage and return the audit record.

        Detects unusual transitions (skipping stages, backward movement,
        moving from terminal states).
        """
        is_unusual = self._is_unusual_transition(new_stage)
        transition = StageTransition(
            opportunity_id=self.id,
            from_stage=self.stage,
            to_stage=new_stage,
            triggered_by=triggered_by,
            is_unusual=is_unusual,
            note=note,
        )
        self.stage = new_stage
        self.touch()
        return transition

    def _is_unusual_transition(self, new_stage: OpportunityStage) -> bool:
        """Check if the transition is unusual (skip, backward, or from terminal).

        Rules:
        - Moving FROM a terminal stage is always unusual.
        - Within STAGE_FLOW: backward or skipping >1 stage is unusual.
        - Going to OFFER without reaching NEGOTIATING first is unusual
          (skipping stages toward a positive outcome).
        """
        if self.stage in TERMINAL_STAGES:
            return True

        if self.stage in STAGE_FLOW and new_stage in STAGE_FLOW:
            from_idx = STAGE_FLOW.index(self.stage)
            to_idx = STAGE_FLOW.index(new_stage)
            if to_idx < from_idx:
                return True
            if to_idx - from_idx > 1:
                return True

        # OFFER should follow NEGOTIATING — skipping to it is unusual
        if new_stage == OpportunityStage.OFFER and self.stage in STAGE_FLOW:
            if self.stage != OpportunityStage.NEGOTIATING:
                return True

        return False

    def accept_stage_suggestion(self) -> StageTransition | None:
        """Accept the AI-suggested stage and clear the suggestion."""
        if self.suggested_stage is None:
            return None
        transition = self.change_stage(
            new_stage=self.suggested_stage,
            triggered_by=TransitionTrigger.USER,
            note=f"Accepted AI suggestion: {self.suggested_stage_reason}",
        )
        self.suggested_stage = None
        self.suggested_stage_reason = None
        return transition

    def dismiss_stage_suggestion(self) -> None:
        """Dismiss the AI-suggested stage without changing."""
        self.suggested_stage = None
        self.suggested_stage_reason = None
        self.touch()

    def record_interaction(self) -> None:
        """Update last_interaction_at timestamp."""
        self.last_interaction_at = datetime.now(UTC)
        self.touch()
