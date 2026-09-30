from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import integrations
from app.config import settings
from app.routers import advisories, parametric, scenarios

app = FastAPI(title=settings.project_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(scenarios.router)
app.include_router(advisories.router)
app.include_router(parametric.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": settings.project_name, "model": settings.gemini_model,
            "demo_mode": integrations.status()["demo_mode"]}
