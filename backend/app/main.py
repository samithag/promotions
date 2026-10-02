from fastapi import FastAPI

app = FastAPI(
    title="Promotions API",
    description="Credit card promotions scraped from Sri Lankan banks.",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
