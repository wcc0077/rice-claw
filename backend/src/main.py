"""FastAPI main application entry point."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .db.database import init_database
from .mcp_server import mcp
from .middleware.observability import ObservabilityMiddleware, BusinessMetricsMiddleware
from .utils.logger import setup_logger

# Initialize logging system
setup_logger()

# Create MCP HTTP app first (needed for lifespan)
# Use stateless_http=True for simpler plugin integration (no session management required)
mcp_app = mcp.http_app(path="/", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: initialize database first
    init_database()
    # Then run MCP lifespan
    async with mcp_app.lifespan(app):
        yield


# Create FastAPI app with combined lifespan (database init + MCP)
app = FastAPI(
    title="Shrimp Market API",
    description="MCP Broker for multi-agent collaboration platform",
    version="0.1.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

# CORS middleware - configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability middleware (must be added AFTER CORS)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(BusinessMetricsMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount MCP server at /mcp endpoint
# OpenClaw agents connect here with their API keys
app.mount("/mcp", mcp_app)


@app.get("/")
async def root():
    return {
        "message": "Shrimp Market API",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp": "/mcp",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - deprecated, use /api/v1/observability/health"""
    from .utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning("/health endpoint is deprecated, use /api/v1/observability/health")

    try:
        from sqlalchemy import text
        from .db.database import engine
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy", "database": db_status}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)