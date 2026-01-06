"""
Seleto Industrial SDR Agent - Entry Point
"""

from agno.os import AgentOS

from src.agents.sdr_agent import create_sdr_agent
from src.api.middleware.logging import LoggingMiddleware
from src.api.middleware.security import SecurityHeadersMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.lgpd import router as lgpd_router
from src.api.routes.metrics import router as metrics_router
from src.api.routes.pending_operations import router as pending_operations_router
from src.api.routes.webhook import router as webhook_router
from src.config.settings import settings
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create SDR agent with system prompt (TECH-010)
sdr_agent = create_sdr_agent()

# AgentOS com FastAPI
agent_os = AgentOS(
    description=settings.APP_NAME,
    id="seleto-sdr",
    agents=[sdr_agent],
)

# Obter app FastAPI
app = agent_os.get_app()

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add security headers middleware (TECH-027)
app.add_middleware(SecurityHeadersMiddleware)

# Registrar rotas customizadas
app.include_router(health_router, tags=["Health"])
app.include_router(webhook_router, tags=["Webhooks"])
app.include_router(metrics_router, tags=["Metrics"])
app.include_router(pending_operations_router, tags=["Pending Operations"])
app.include_router(lgpd_router, tags=["LGPD"])

# Log startup
logger.info(
    f"Application started: {settings.APP_NAME}",
    extra={
        "app_env": settings.APP_ENV,
        "debug": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
    },
)

if __name__ == "__main__":
    agent_os.serve(
        app="src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
