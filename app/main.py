import uuid
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import pymentor_agent
from app.config import (
    GEMINI_MODEL,
    HOST,
    PORT,
    STATIC_DIR,
    MODEL_FALLBACK_CASCADE,
    is_api_key_valid,
)
from app.database import (
    get_analytics_summary,
    get_recent_logs,
    get_session_logs,
    init_db,
)
from app.memory import memory_manager
from app.prompt_builder import load_knowledge_base

logger = logging.getLogger("pymentor.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    pymentor_agent.refresh_knowledge()
    logger.info("PyMentor started with Multi-Model Fallback Engine.")
    yield
    logger.info("PyMentor shutting down.")

app = FastAPI(
    title="PyMentor API",
    description="Domain-restricted virtual assistant and tutor for Python code understanding",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or Python code snippet")
    session_id: Optional[str] = Field(None, description="Unique conversation session identifier")
    force_mock: Optional[bool] = Field(False, description="Optionally force mock response mode for testing")

class ChatResponse(BaseModel):
    session_id: str
    response: str
    response_time_ms: float
    tokens_used: int
    status: str
    model_used: Optional[str] = Field("gemini", description="The specific Gemini model that served this query")

class ResetSessionRequest(BaseModel):
    session_id: str

@app.get("/", response_class=FileResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI index.html not found")
    return FileResponse(index_file)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    session_id = payload.session_id.strip() if payload.session_id else str(uuid.uuid4())
    user_msg = payload.message.strip()

    if not user_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty. Please provide a Python question or code snippet."
        )

    result = pymentor_agent.process_message(
        session_id=session_id,
        user_message=user_msg,
        force_mock=payload.force_mock or False
    )

    return ChatResponse(
        session_id=result["session_id"],
        response=result["response"],
        response_time_ms=result["response_time_ms"],
        tokens_used=result["tokens_used"],
        status=result["status"],
        model_used=result.get("model_used", "gemini")
    )

@app.post("/api/session/reset")
async def reset_session_endpoint(payload: ResetSessionRequest):
    session_id = payload.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    memory_manager.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} memory cleared."}

@app.get("/api/session/{session_id}/history")
async def get_session_history_endpoint(session_id: str):
    history = memory_manager.get_history(session_id)
    return {"session_id": session_id, "turns": history, "count": len(history)}

@app.get("/api/logs")
async def get_logs_endpoint(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session_id: Optional[str] = None
):
    if session_id:
        logs = get_session_logs(session_id)
    else:
        logs = get_recent_logs(limit=limit, offset=offset)
    return {"logs": logs, "count": len(logs)}

@app.get("/api/logs/analytics")
async def get_analytics_endpoint():
    analytics = get_analytics_summary()
    return analytics

@app.get("/api/knowledge")
async def get_knowledge_summary():
    content = load_knowledge_base()
    sections = [
        line.replace("#", "").strip()
        for line in content.splitlines()
        if line.startswith("## ") or line.startswith("### ")
    ]
    return {
        "status": "loaded",
        "length_chars": len(content),
        "sections": sections
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "PyMentor",
        "primary_model": GEMINI_MODEL,
        "fallback_cascade": MODEL_FALLBACK_CASCADE,
        "api_key_configured": is_api_key_valid(),
        "database": "sqlite_ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
