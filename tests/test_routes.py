"""End-to-end tests for the FastAPI routes."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_navigate_and_fill_form_no_hil(client, test_server):
    """Navigate + fill_form (no HiL) -> completed."""
    response = client.post("/execute", json={
        "steps": [
            {"type": "navigate", "url": test_server},
            {"type": "fill_form", "title": "Registration", "fields": {"firstname": "Jane", "lastname": "Doe"}},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 2
    assert data["results"][0]["status"] == "success"
    assert data["results"][1]["status"] == "success"


def test_navigate_and_click_link(client, test_server):
    """Navigate + click link -> completed."""
    response = client.post("/execute", json={
        "steps": [
            {"type": "navigate", "url": test_server},
            {"type": "click", "target": "link", "name": "Next Page"},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 2
    assert "Next Page" in data["results"][1]["detail"]


def test_navigate_and_click_button(client, test_server):
    """Navigate + click button -> completed."""
    response = client.post("/execute", json={
        "steps": [
            {"type": "navigate", "url": test_server},
            {"type": "click", "target": "button", "name": "Submit"},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 2


def test_hil_continue_flow(client, test_server):
    """HiL flow: navigate + fill_form(hil=true) -> waiting -> continue -> completed."""
    # Step 1: Start execution with HiL
    response = client.post("/execute", json={
        "steps": [
            {"type": "navigate", "url": test_server},
            {"type": "fill_form", "title": "Registration", "fields": {"firstname": "Jane", "lastname": "Doe"}, "hil": True},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_for_confirmation"
    assert data["execution_id"] is not None
    assert data["pending_step"] is not None
    assert data["pending_step"]["step_index"] == 1

    execution_id = data["execution_id"]

    # Step 2: Continue
    response = client.post(f"/execute/continue/{execution_id}", json={
        "action": "continue"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 2
    assert data["results"][1]["status"] == "success"


def test_hil_cancel_flow(client, test_server):
    """HiL cancel: navigate + fill_form(hil=true) -> waiting -> cancel -> skipped."""
    # Step 1: Start execution with HiL
    response = client.post("/execute", json={
        "steps": [
            {"type": "navigate", "url": test_server},
            {"type": "fill_form", "title": "Registration", "fields": {"firstname": "Jane", "lastname": "Doe"}, "hil": True},
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_for_confirmation"
    execution_id = data["execution_id"]

    # Step 2: Cancel
    response = client.post(f"/execute/continue/{execution_id}", json={
        "action": "cancel"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["results"][1]["status"] == "skipped"
    assert "cancelled" in data["results"][1]["detail"].lower()


def test_continue_nonexistent_execution(client):
    """Continue on non-existent execution returns 404."""
    response = client.post("/execute/continue/nonexistent-id", json={
        "action": "continue"
    })
    assert response.status_code == 404
