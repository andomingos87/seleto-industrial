"""
Seleto Industrial SDR Agent - Entry Point
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

from src.api.middleware.logging import LoggingMiddleware
from src.api.routes.health import router as health_router
from src.config.settings import settings
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Placeholder agent (será expandido em TECH-009/TECH-010)
sdr_agent = Agent(
    name="Seleto SDR",
    model=OpenAIChat(id=settings.OPENAI_MODEL),
    description="Agente de qualificação de leads para Seleto Industrial",
    instructions=[
        "Você é um assistente de vendas da Seleto Industrial.",
        "Sua função é qualificar leads e coletar informações relevantes.",
    ],
    markdown=True,
)

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
