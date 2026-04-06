"""FastAPI routes for the Browser Automation Service."""

from fastapi import APIRouter, HTTPException

from src.dto import ExecuteRequest, ExecuteResponse, ContinueRequest
from src.executor import Executor

router = APIRouter()
executor = Executor()


@router.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest) -> ExecuteResponse:
    """Execute a sequence of browser automation steps."""
    try:
        return executor.execute(request.steps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/execute/continue/{execution_id}", response_model=ExecuteResponse)
def continue_execution(execution_id: str, request: ContinueRequest) -> ExecuteResponse:
    """Resume a paused execution after Human-in-the-Loop confirmation."""
    try:
        return executor.continue_execution(execution_id, request.action)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
