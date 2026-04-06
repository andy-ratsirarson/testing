"""Browser Automation Service entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.routes import router

app = FastAPI(title="Browser Automation Service")
app.include_router(router)

# Sample HTML page for manual testing
SAMPLE_HTML = (Path(__file__).parent.parent / "tests" / "sample.html").read_text()


@app.get("/sample", response_class=HTMLResponse)
def sample_page():
    """Serve the sample registration form."""
    return SAMPLE_HTML


@app.post("/submit", response_class=HTMLResponse)
def sample_submit():
    """Handle sample form submission."""
    return "<html><body><h1>Submission successful</h1></body></html>"


@app.get("/next", response_class=HTMLResponse)
def sample_next():
    """Serve the sample next page."""
    return "<html><body><h1>Next Page</h1></body></html>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
