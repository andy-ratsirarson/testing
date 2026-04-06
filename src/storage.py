"""Markdown file-based persistence for execution state."""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Optional


EXECUTIONS_DIR = Path("executions")


class ExecutionStorage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or EXECUTIONS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, execution_id: str) -> Path:
        return self.base_dir / f"{execution_id}.md"

    def _write(
        self,
        execution_id: str,
        steps: list[dict],
        current_step: int,
        status: str,
        results: list[dict],
        pending_data: Optional[dict] = None,
    ) -> None:
        """Write execution state as markdown with JSON blocks."""
        content = f"# Execution {execution_id}\n\n"
        content += f"## Status\n\n{status}\n\n"
        content += f"## Current Step\n\n{current_step}\n\n"
        content += "## Steps\n\n```json\n"
        content += json.dumps(steps, indent=2)
        content += "\n```\n\n"
        content += "## Results\n\n```json\n"
        content += json.dumps(results, indent=2)
        content += "\n```\n\n"
        content += "## Pending Data\n\n```json\n"
        content += json.dumps(pending_data, indent=2)
        content += "\n```\n"

        self._file_path(execution_id).write_text(content)

    def create(
        self,
        steps: list[dict],
        current_step: int,
        status: str,
        results: list[dict],
        pending_data: Optional[dict] = None,
    ) -> str:
        """Create a new execution record. Returns execution_id."""
        execution_id = str(uuid.uuid4())
        self._write(execution_id, steps, current_step, status, results, pending_data)
        return execution_id

    def load(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Parse .md file back to dict. Returns None if not found."""
        path = self._file_path(execution_id)
        if not path.exists():
            return None

        content = path.read_text()
        data: dict[str, Any] = {"execution_id": execution_id}

        # Parse status
        status_marker = "## Status\n\n"
        idx = content.find(status_marker)
        if idx != -1:
            rest = content[idx + len(status_marker):]
            data["status"] = rest[: rest.index("\n\n")].strip()

        # Parse current_step
        step_marker = "## Current Step\n\n"
        idx = content.find(step_marker)
        if idx != -1:
            rest = content[idx + len(step_marker):]
            data["current_step"] = int(rest[: rest.index("\n\n")].strip())

        # Parse JSON blocks
        json_sections = ["Steps", "Results", "Pending Data"]
        json_keys = ["steps", "results", "pending_data"]
        for section, key in zip(json_sections, json_keys):
            marker = f"## {section}\n\n```json\n"
            idx = content.find(marker)
            if idx != -1:
                rest = content[idx + len(marker):]
                json_str = rest[: rest.index("\n```")]
                data[key] = json.loads(json_str)

        return data

    def update(self, execution_id: str, **kwargs: Any) -> None:
        """Update fields in an existing execution."""
        data = self.load(execution_id)
        if data is None:
            raise FileNotFoundError(f"Execution {execution_id} not found")

        for key, value in kwargs.items():
            data[key] = value

        self._write(
            execution_id,
            data["steps"],
            data["current_step"],
            data["status"],
            data["results"],
            data.get("pending_data"),
        )

    def delete(self, execution_id: str) -> None:
        """Remove .md file."""
        path = self._file_path(execution_id)
        if path.exists():
            os.remove(path)
