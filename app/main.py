from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.database import lifespan
from app.config import settings
from app.router import router as document_router # Import our router

app = FastAPI(
    title="RFP Response Accelerator",
    version="1.0.0",
    lifespan=lifespan
)

UI_DIRECTORY = Path(__file__).resolve().parent / "static"
app.mount("/ui/static", StaticFiles(directory=UI_DIRECTORY), name="ui-static")

# Attach ingestion endpoints to the application core
app.include_router(document_router)


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def get_ui() -> HTMLResponse:
    """Serve the public, same-origin RFP answer interface."""
    return HTMLResponse((UI_DIRECTORY / "index.html").read_text(encoding="utf-8"))


@app.get("/health", status_code=status.HTTP_200_OK, include_in_schema=False)
async def health_check():
    """Liveness probe that does not depend on the database or AI providers."""
    return {"status": "healthy"}


@app.get("/", status_code=status.HTTP_200_OK)
async def get_system_status():
    """Returns application metadata safely without exposing secret keys."""
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "embedding_engine": settings.EMBEDDING_MODEL
    }
