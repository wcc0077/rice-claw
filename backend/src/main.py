"""FastAPI main application entry point."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .db.database import init_database
from .mcp_server import mcp

# Create MCP HTTP app first (needed for lifespan)
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    init_database()
    yield
    # Shutdown (if needed)


# Create FastAPI app with MCP lifespan for session management
app = FastAPI(
    title="Shrimp Market API",
    description="MCP Broker for multi-agent collaboration platform",
    version="0.1.0",
    redirect_slashes=False,
    lifespan=mcp_app.lifespan,
)

# CORS middleware - configure for production
# TODO: Replace allow_origins=["*"] with specific allowed origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Health check endpoint with database status."""
    try:
        from sqlalchemy import text
        from .db.database import engine
        from sqlalchemy import text
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy", "database": db_status}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)