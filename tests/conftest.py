"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_session_config():
    """Mock SessionConfig for testing."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.data_dir = Path("/mock/session/data")
    mock.db_path = Path("/mock/session/data/sql/db.sqlite")
    mock.config_path = Path("/mock/session/data/config.json")
    return mock
