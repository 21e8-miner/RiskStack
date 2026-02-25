from fastapi import FastAPI

from .api.health import router as health_router
from .api.auth import router as auth_router
from .api.clients import router as clients_router
from .api.portfolios import router as portfolios_router
from .api.analytics import router as analytics_router
from .api.ingestion import router as ingestion_router
from .api.proposals import router as proposals_router

app = FastAPI(title="RiskStack API", version="0.1.0")

app.include_router(health_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(clients_router, prefix="/v1")
app.include_router(portfolios_router, prefix="/v1")
app.include_router(analytics_router, prefix="/v1")
app.include_router(ingestion_router, prefix="/v1")
app.include_router(proposals_router, prefix="/v1")
