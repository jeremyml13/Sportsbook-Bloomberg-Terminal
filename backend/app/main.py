from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import games, ingest
from app.core.config import settings

app = FastAPI(
    title="Sports Betting Market Terminal API",
    description="Market intelligence API for odds movement, volatility, and book disagreement.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(ingest.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
