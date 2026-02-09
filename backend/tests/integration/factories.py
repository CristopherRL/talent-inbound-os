"""Factory-boy factories for integration test data."""

import factory

from talent_inbound.shared.domain.enums import (
    InteractionSource,
    InteractionType,
    OpportunityStatus,
    ProcessingStatus,
    WorkModel,
)


class CandidateFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Faker("uuid4")
    email = factory.Faker("email")
    hashed_password = "bcrypt$fakehash"
    is_active = True


class CandidateProfileFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Faker("uuid4")
    candidate_id = factory.Faker("uuid4")
    display_name = factory.Faker("name")
    professional_title = "Senior Backend Engineer"
    skills = ["Python", "FastAPI", "PostgreSQL"]
    min_salary = 80000
    preferred_currency = "EUR"
    work_model = WorkModel.REMOTE
    preferred_locations = ["Spain", "EU Remote"]
    industries = ["FinTech", "HealthTech"]
    cv_filename = None
    cv_storage_path = None
    cv_extracted_text = None
    follow_up_days = 7
    ghosting_days = 14


class InteractionFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Faker("uuid4")
    candidate_id = factory.Faker("uuid4")
    opportunity_id = None
    raw_content = factory.Faker("paragraph", nb_sentences=5)
    sanitized_content = None
    source = InteractionSource.LINKEDIN
    interaction_type = InteractionType.INITIAL
    processing_status = ProcessingStatus.PENDING
    classification = None
    pipeline_log = []


class OpportunityFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Faker("uuid4")
    candidate_id = factory.Faker("uuid4")
    company_name = factory.Faker("company")
    client_name = None
    role_title = factory.Iterator([
        "Senior Backend Engineer",
        "Staff Engineer",
        "Principal Engineer",
        "Tech Lead",
    ])
    salary_range = "80000-120000 EUR"
    tech_stack = ["Python", "FastAPI", "PostgreSQL"]
    work_model = WorkModel.REMOTE
    recruiter_name = factory.Faker("name")
    recruiter_type = "AGENCY"
    recruiter_company = factory.Faker("company")
    match_score = factory.Faker("random_int", min=0, max=100)
    match_reasoning = None
    missing_fields = []
    status = OpportunityStatus.NEW
    is_archived = False
