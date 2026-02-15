"""Shared domain enums for the Talent Inbound OS."""

from enum import StrEnum


class OpportunityStatus(StrEnum):
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    REVIEWING = "REVIEWING"
    INTERVIEWING = "INTERVIEWING"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    GHOSTED = "GHOSTED"


TERMINAL_STATUSES = frozenset({
    OpportunityStatus.OFFER,
    OpportunityStatus.REJECTED,
    OpportunityStatus.GHOSTED,
})

STANDARD_FLOW = [
    OpportunityStatus.NEW,
    OpportunityStatus.ANALYZING,
    OpportunityStatus.ACTION_REQUIRED,
    OpportunityStatus.REVIEWING,
    OpportunityStatus.INTERVIEWING,
]


class InteractionSource(StrEnum):
    LINKEDIN = "LINKEDIN"
    EMAIL = "EMAIL"
    FREELANCE_PLATFORM = "FREELANCE_PLATFORM"
    OTHER = "OTHER"
    CHAT_FOLLOWUP = "CHAT_FOLLOWUP"


class InteractionType(StrEnum):
    INITIAL = "INITIAL"
    FOLLOW_UP = "FOLLOW_UP"
    CANDIDATE_RESPONSE = "CANDIDATE_RESPONSE"


class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Classification(StrEnum):
    REAL_OFFER = "REAL_OFFER"
    SPAM = "SPAM"
    NOT_AN_OFFER = "NOT_AN_OFFER"


class WorkModel(StrEnum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"


class RecruiterType(StrEnum):
    AGENCY = "AGENCY"
    HEADHUNTER = "HEADHUNTER"
    DIRECT_CLIENT = "DIRECT_CLIENT"
    PLATFORM = "PLATFORM"


class ResponseType(StrEnum):
    REQUEST_INFO = "REQUEST_INFO"
    EXPRESS_INTEREST = "EXPRESS_INTEREST"
    DECLINE = "DECLINE"


class TransitionTrigger(StrEnum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    CHAT = "CHAT"


class ChatRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
