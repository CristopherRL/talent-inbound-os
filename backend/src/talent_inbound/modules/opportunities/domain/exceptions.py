"""Domain exceptions for the opportunities module."""


class OpportunityNotFoundError(Exception):
    """Raised when an opportunity is not found."""

    def __init__(self, opportunity_id: str) -> None:
        self.opportunity_id = opportunity_id
        super().__init__(f"Opportunity not found: {opportunity_id}")
