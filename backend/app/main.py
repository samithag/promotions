from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as api_v1
from app.db import get_sessionmaker
from app.services.banks import sync_banks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Tests set their own session factory before startup.
    if not hasattr(app.state, "session_factory"):
        app.state.session_factory = get_sessionmaker()
    with app.state.session_factory() as session:
        sync_banks(session)
    yield


app = FastAPI(
    title="Promotions API",
    description="Credit card promotions scraped from Sri Lankan banks.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(api_v1)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
