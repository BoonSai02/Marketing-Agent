from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend_config import Backend_config
from routes.auth import router as auth_router
from routes.agent import router as agent_router
import logging
import uvicorn

settings = Backend_config()

# configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("unified.main")

from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agent_src.orchestrator.orchestrator_graph import compile_workflow

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize AsyncSqliteSaver and compile graph
    async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
        logger.info("Initializing AsyncSqliteSaver...")
        graph_app = compile_workflow(checkpointer)
        app.state.graph_app = graph_app
        yield
        # Shutdown: Connection is closed automatically by context manager
        logger.info("Closing AsyncSqliteSaver...")

app = FastAPI(
    title="Unified Marketing Agent API",
    description="Unified API for User Authentication and AI Marketing Agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for now to support both local dev environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)


@app.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy", "message": "Unified API is running"})


@app.get("/")
async def root():
    return JSONResponse(status_code=200, content={"message": "Welcome to Unified Marketing Agent API", "version": "1.0.0", "docs": "/docs"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
