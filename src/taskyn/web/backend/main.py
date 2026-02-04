"""FastAPI application — thin REST bridge to MCP tools."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.auth import router as auth_router

app = FastAPI(
    title="Taskyn API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
