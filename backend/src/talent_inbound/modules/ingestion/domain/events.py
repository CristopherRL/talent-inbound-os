"""Domain events for the ingestion module."""

from talent_inbound.shared.domain.events import DomainEvent


class InteractionCreated(DomainEvent):
    """Fired when a new Interaction is submitted."""

    interaction_id: str
    opportunity_id: str
    candidate_id: str
