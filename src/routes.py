"""FastAPI routes for the Browser Automation Service."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.dto import ExecuteRequest, ExecuteResponse, ContinueRequest
from src.executor import Executor

router = APIRouter()
executor = Executor()

SAMPLE_HTML = Path(__file__).resolve().parent.parent / "tests" / "sample.html"


@router.get("/sample", response_class=HTMLResponse)
def sample():
    """Serve the example home page."""
    return SAMPLE_HTML.read_text()


@router.post("/submit", response_class=HTMLResponse)
async def submit(request: Request):
    """Handle sample form submission and log to submissions folder."""
    import uuid
    from datetime import datetime
    from urllib.parse import parse_qs

    body = (await request.body()).decode()
    fields = {k: v[0] for k, v in parse_qs(body).items()}

    # Save submission to md file
    sub_dir = Path(__file__).resolve().parent.parent / "submissions"
    sub_dir.mkdir(exist_ok=True)
    sub_id = str(uuid.uuid4())
    content = f"# Submission {sub_id}\n\n"
    content += f"**Timestamp**: {datetime.now().isoformat()}\n\n"
    content += "## Fields\n\n"
    for k, v in fields.items():
        content += f"- **{k}**: {v}\n"
    (sub_dir / f"{sub_id}.md").write_text(content)

    items = "".join(f"<li><b>{k}</b>: {v}</li>" for k, v in fields.items())
    return f"<html><body><h1>Form Submitted Successfully</h1><ul>{items}</ul></body></html>"


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
