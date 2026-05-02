"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import router

app = FastAPI(
    title="Multi-Agent Code Review Agent",
    version="0.1.0",
    description="Diff review workflow with static tools, specialist reviewers, and a supervisor.",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
