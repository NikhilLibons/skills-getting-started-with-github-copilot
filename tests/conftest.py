"""Pytest configuration and shared fixtures for FastAPI tests."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for making HTTP requests to the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities to a known clean state before each test.
    This fixture saves the original state and restores it after the test.
    """
    # Save original activities state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy(),
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)
