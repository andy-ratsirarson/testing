"""Data Transfer Objects for the Browser Automation Service."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class StepType(str, Enum):
    navigate = "navigate"
    fill_form = "fill_form"
    click = "click"


class ClickTarget(str, Enum):
    button = "button"
    link = "link"


class Step(BaseModel):
    type: StepType
    url: Optional[str] = None
    title: Optional[str] = None
    fields: Optional[dict[str, str]] = None
    hil: Optional[bool] = False
    target: Optional[ClickTarget] = None
    name: Optional[str] = None


class ExecuteRequest(BaseModel):
    steps: list[Step]


class ContinueRequest(BaseModel):
    action: str  # "continue" or "cancel"


class StepResult(BaseModel):
    step_index: int
    type: StepType
    status: str
    detail: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: Optional[str] = None
    status: str
    results: list[StepResult] = []
    pending_step: Optional[dict] = None
