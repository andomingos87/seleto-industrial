"""
Seleto Industrial SDR Agent - Entry Point
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

from src.api.middleware.logging import LoggingMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.webhook import router as webhook_router
from src.agents.sdr_agent import create_sdr_agent
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

# Registrar rotas customizadas
app.include_router(health_router, tags=["Health"])
app.include_router(webhook_router, tags=["Webhooks"])

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
