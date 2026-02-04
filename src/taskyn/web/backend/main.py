"""FastAPI application — thin REST bridge to MCP tools."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.activity import router as activity_router
from .routes.auth import router as auth_router
from .routes.companies import router as companies_router
from .routes.dashboard import router as dashboard_router
from .routes.edges import router as edges_router
from .routes.milestones import router as milestones_router
from .routes.nodes import router as nodes_router
from .routes.projects import router as projects_router
from .routes.search import router as search_router
from .routes.tags import router as tags_router
from .routes.time_entries import router as time_entries_router
from .routes.timer import router as timer_router

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
app.include_router(companies_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(nodes_router, prefix="/api/v1")
app.include_router(edges_router, prefix="/api/v1")
app.include_router(milestones_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(timer_router, prefix="/api/v1")
app.include_router(time_entries_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
