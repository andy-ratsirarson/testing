"""Executor engine: orchestrates step execution with Human-in-the-Loop support."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.dto import Step, StepType, StepResult, ExecuteResponse
from src.storage import ExecutionStorage
from src.steps.navigate import execute_navigate
from src.steps.fill_form import find_form_by_title, build_form_data, submit_form
from src.steps.click import execute_click


class Executor:
    def __init__(self):
        self.storage = ExecutionStorage()

    def execute(self, steps: list[Step]) -> ExecuteResponse:
        """Run steps sequentially. On HiL fill_form: persist state and return waiting response."""
        session = requests.Session()
        current_soup: BeautifulSoup | None = None
        current_url: str = ""
        results: list[StepResult] = []

        for i, step in enumerate(steps):
            result = self._execute_step(
                index=i,
                step=step,
                session=session,
                soup=current_soup,
                current_url=current_url,
                steps=steps,
                results=results,
            )

            if isinstance(result, ExecuteResponse):
                # HiL pause -- return immediately
                return result

            step_result, current_soup, current_url = result
            results.append(step_result)

        return ExecuteResponse(
            status="completed",
            results=results,
        )

    def _execute_step(
        self,
        index: int,
        step: Step,
        session: requests.Session,
        soup: BeautifulSoup | None,
        current_url: str,
        steps: list[Step],
        results: list[StepResult],
    ) -> ExecuteResponse | tuple[StepResult, BeautifulSoup | None, str]:
        """Execute a single step. Returns ExecuteResponse for HiL pause,
        or (StepResult, soup, url) for normal completion."""

        if step.type == StepType.navigate:
            if not step.url:
                raise ValueError(f"Step {index}: navigate requires a url")
            new_soup, new_url = execute_navigate(step.url, session)
            return (
                StepResult(step_index=index, type=step.type, status="success", detail=f"Navigated to {new_url}"),
                new_soup,
                new_url,
            )

        elif step.type == StepType.fill_form:
            if soup is None:
                raise ValueError(f"Step {index}: fill_form requires a prior navigate step")
            if not step.title:
                raise ValueError(f"Step {index}: fill_form requires a title")

            form = find_form_by_title(soup, step.title)
            if form is None:
                raise ValueError(f"Step {index}: no form found matching title '{step.title}'")

            fields = step.fields or {}
            action_url, form_data = build_form_data(form, fields)

            if step.hil:
                # Human-in-the-Loop: persist state and return
                steps_dicts = [s.model_dump(mode="json") for s in steps]
                results_dicts = [r.model_dump(mode="json") for r in results]
                pending_data = {
                    "action_url": action_url,
                    "form_data": form_data,
                    "base_url": current_url,
                    "step_index": index,
                }
                execution_id = self.storage.create(
                    steps=steps_dicts,
                    current_step=index,
                    status="waiting_for_confirmation",
                    results=results_dicts,
                    pending_data=pending_data,
                )
                return ExecuteResponse(
                    execution_id=execution_id,
                    status="waiting_for_confirmation",
                    results=results,
                    pending_step={
                        "step_index": index,
                        "type": step.type.value,
                        "title": step.title,
                        "fields": fields,
                        "action_url": action_url,
                    },
                )

            # Submit immediately
            new_soup = submit_form(session, action_url, form_data, current_url)
            return (
                StepResult(step_index=index, type=step.type, status="success", detail=f"Form '{step.title}' submitted"),
                new_soup,
                current_url,
            )

        elif step.type == StepType.click:
            if soup is None:
                raise ValueError(f"Step {index}: click requires a prior navigate step")
            if not step.target or not step.name:
                raise ValueError(f"Step {index}: click requires target and name")

            click_result = execute_click(soup, step.target.value, step.name, session, current_url)
            if click_result is None:
                raise ValueError(f"Step {index}: could not find {step.target.value} '{step.name}'")

            new_soup, new_url = click_result
            return (
                StepResult(
                    step_index=index,
                    type=step.type,
                    status="success",
                    detail=f"Clicked {step.target.value} '{step.name}'",
                ),
                new_soup,
                new_url,
            )

        raise ValueError(f"Step {index}: unknown step type '{step.type}'")

    def continue_execution(self, execution_id: str, action: str) -> ExecuteResponse:
        """Resume a paused execution.

        Since requests.Session cannot be persisted, we:
        1. Load state from storage
        2. Create a new Session
        3. Re-execute navigate steps up to the paused point to rebuild cookies
        4. Submit (or skip) the pending form
        5. Continue remaining steps
        6. Clean up storage
        """
        data = self.storage.load(execution_id)
        if data is None:
            raise FileNotFoundError(f"Execution {execution_id} not found")

        steps = [Step(**s) for s in data["steps"]]
        current_step = data["current_step"]
        pending_data = data.get("pending_data", {})
        results = [StepResult(**r) for r in data["results"]]

        session = requests.Session()
        current_soup: BeautifulSoup | None = None
        current_url: str = ""

        # Replay navigate steps up to the paused point to rebuild session state
        for i in range(current_step):
            step = steps[i]
            if step.type == StepType.navigate and step.url:
                current_soup, current_url = execute_navigate(step.url, session)

        if action == "continue":
            # Submit the pending form
            action_url = pending_data.get("action_url", "")
            form_data = pending_data.get("form_data", {})
            base_url = pending_data.get("base_url", current_url)

            current_soup = submit_form(session, action_url, form_data, base_url)
            results.append(
                StepResult(
                    step_index=current_step,
                    type=StepType.fill_form,
                    status="success",
                    detail=f"Form submitted after confirmation",
                )
            )
        elif action == "cancel":
            results.append(
                StepResult(
                    step_index=current_step,
                    type=StepType.fill_form,
                    status="skipped",
                    detail="Step cancelled by user",
                )
            )
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'continue' or 'cancel'.")

        # Continue remaining steps
        for i in range(current_step + 1, len(steps)):
            step = steps[i]
            result = self._execute_step(
                index=i,
                step=step,
                session=session,
                soup=current_soup,
                current_url=current_url,
                steps=steps,
                results=results,
            )

            if isinstance(result, ExecuteResponse):
                # Another HiL pause
                self.storage.delete(execution_id)
                return result

            step_result, current_soup, current_url = result
            results.append(step_result)

        # Clean up
        self.storage.delete(execution_id)

        return ExecuteResponse(
            status="completed",
            results=results,
        )
