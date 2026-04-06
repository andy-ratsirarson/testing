"""Tests for the markdown-based execution storage."""

import tempfile
from pathlib import Path

import pytest

from src.storage import ExecutionStorage


@pytest.fixture
def storage(tmp_path):
    return ExecutionStorage(base_dir=tmp_path)


def test_create_and_load(storage):
    """Round-trip: create an execution and load it back."""
    steps = [{"type": "navigate", "url": "http://example.com"}]
    results = [{"step_index": 0, "type": "navigate", "status": "success"}]

    eid = storage.create(
        steps=steps,
        current_step=0,
        status="completed",
        results=results,
        pending_data={"key": "value"},
    )

    data = storage.load(eid)
    assert data is not None
    assert data["execution_id"] == eid
    assert data["status"] == "completed"
    assert data["current_step"] == 0
    assert data["steps"] == steps
    assert data["results"] == results
    assert data["pending_data"] == {"key": "value"}


def test_update(storage):
    """Update fields in an existing execution."""
    eid = storage.create(
        steps=[],
        current_step=0,
        status="running",
        results=[],
    )

    storage.update(eid, status="completed", current_step=3)

    data = storage.load(eid)
    assert data["status"] == "completed"
    assert data["current_step"] == 3


def test_delete(storage):
    """Remove an execution file."""
    eid = storage.create(steps=[], current_step=0, status="running", results=[])

    storage.delete(eid)
    assert storage.load(eid) is None


def test_load_nonexistent(storage):
    """Loading a non-existent execution returns None."""
    assert storage.load("nonexistent-id-12345") is None
