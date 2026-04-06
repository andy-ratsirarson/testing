"""Browser Automation Service entrypoint."""

from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="Browser Automation Service")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
