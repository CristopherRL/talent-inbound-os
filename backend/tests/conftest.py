"""Root-level shared test fixtures."""

import pytest


@pytest.fixture
def sample_email() -> str:
    return "senior.engineer@example.com"


@pytest.fixture
def sample_password() -> str:
    return "Str0ngP@ssword!"
