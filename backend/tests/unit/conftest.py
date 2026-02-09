"""Unit test fixtures. Mock all external dependencies."""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    bus.publish_all = AsyncMock()
    return bus
