import uuid
import logging
import asyncio
import json
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Security, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlmodel import Session
import os

from codelens_env.models import (
    TaskId, Action, ResetResult, StepResult, EpisodeResult, ActionRecord, Observation
)
from codelens_env.env import CodeLensEnv
from codelens_env.config import get_settings
from codelens_env.database import (
    create_db_and_tables, get_session, save_episode,
    get_episode, get_leaderboard_db, submit_leaderboard, get_stats,
    LeaderboardRecord
)

# ── Logging ───────────────────────────────────────────────────────────────────
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codelens_env")

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not os.getenv("TESTING"):
        create_db_and_tables()
        logger.info(f"CodeLens API started — DB at {settings.db_path}")
    else:
        logger.info("CodeLens API running in TESTING mode — DB initialization skipped")

    cleanup_task = asyncio.create_task(cleanup_expired_episodes())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("CodeLens API shutting down")

# ── App Initialization ────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeLens API",
    description=(
        "AI Senior Code Reviewer evaluation environment. "
        "Trains agents to detect bugs, security vulnerabilities, and architectural issues "
        "in realistic Python PRs."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Security & Middleware ──────────────────────────────────────────────────
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# 1. Trusted Host (Prevent Host-header injection)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"] if settings.app_env in ("development", "test") else [f"localhost", "127.0.0.1", "*.github.io", "testserver"] 
)

# 2. Proxy Headers (Support Docker/Reverse-proxy)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [f"http://localhost:{settings.app_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:;"
    return response

# 5. Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── API Key Authentication ────────────────────────────────────────────────────
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not settings.api_key_enabled:
        return  # Auth disabled in development
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

# ── Storage & TTL ─────────────────────────────────────────────────────────────
episodes: Dict[str, CodeLensEnv] = {}
episode_timestamps: Dict[str, datetime] = {}

async def cleanup_expired_episodes():
    """Remove episodes older than TTL."""
    while True:
        await asyncio.sleep(300)  # run every 5 minutes
        cutoff = datetime.now(timezone.utc).timestamp() - settings.episode_ttl_seconds
        expired = [
            eid for eid, ts in episode_timestamps.items()
            if ts.timestamp() < cutoff
        ]
        for eid in expired:
            episodes.pop(eid, None)
            episode_timestamps.pop(eid, None)
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired episodes")


# ── Models ────────────────────────────────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: TaskId
    seed:    int = 42

class ResetResponse(BaseModel):
    episode_id: str
    result:     ResetResult

class SubmitScore(BaseModel):
    agent_name: str
    task_id:    TaskId
    score:      float
    seed:       int

# ── WebSocket clients ─────────────────────────────────────────────────────────
clients = set()

async def broadcast_event(data: dict):
    from fastapi.encoders import jsonable_encoder
    message = json.dumps(jsonable_encoder(data))
    dead = set()
    for client in clients:
        try:
            await client.send_text(message)
        except Exception:
            dead.add(client)
    clients.difference_update(dead)

# ── Error Handlers ────────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": str(exc),
            "status_code": 422
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} \u2014 {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "env_ready": True,
        "env": settings.app_env,
        "active_episodes": len(episodes),
        "auth_enabled": settings.api_key_enabled,
        "dashboard_url": "/dashboard"
    }

@app.post("/reset", response_model=ResetResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def reset_env(request: Request, req: ResetRequest, _: None = Depends(verify_api_key)):
    episode_id = str(uuid.uuid4())
    env        = CodeLensEnv()
    result     = env.reset(req.task_id, req.seed)
    episodes[episode_id] = env
    episode_timestamps[episode_id] = datetime.now(timezone.utc)
    return ResetResponse(episode_id=episode_id, result=result)

@app.post("/step/{episode_id}", response_model=StepResult)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def step_env(request: Request, episode_id: str, action: Action, _: None = Depends(verify_api_key)):
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")

    env = episodes[episode_id]
    try:
        result = env.step(action)
        await broadcast_event({"episode_id": episode_id, "type": "step", "reward": result.reward})
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state/{episode_id}", response_model=Observation)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def get_state(request: Request, episode_id: str, _: None = Depends(verify_api_key)):
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    env = episodes[episode_id]
    return env._build_observation()

@app.get("/result/{episode_id}", response_model=EpisodeResult)
def get_result(
    episode_id: str,
    session: Session = Depends(get_session),
    _: None = Depends(verify_api_key)
):
    # Try in-memory (active episode)
    if episode_id in episodes:
        env = episodes[episode_id]
        result = env.get_final_result()
        result.episode_id = episode_id
        # If done, persist and remove from memory
        if env.done:
            save_episode(session, result)
            del episodes[episode_id]
            episode_timestamps.pop(episode_id, None)
        return result
    
    # Fall back to DB (completed episode)
    record = get_episode(session, episode_id)
    if not record:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    return EpisodeResult(
        episode_id=record.episode_id,
        task_id=TaskId(record.task_id),
        scenario_hash=record.scenario_hash,
        seed=record.seed,
        final_score=record.final_score,
        steps_taken=record.steps_taken,
        issues_found=record.issues_found,
        issues_total=record.issues_total,
        noise_penalties=record.noise_penalties,
        terminated_reason=record.terminated_reason,
        history=[ActionRecord(**r) for r in json.loads(record.history_json or "[]")]
    )

@app.get("/leaderboard")
def get_leaderboard(
    task_id: Optional[TaskId] = None,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session)
):
    tasks_to_query = [task_id] if task_id else list(TaskId)
    result = {}
    for t in tasks_to_query:
        entries, total = get_leaderboard_db(session, t.value, limit, offset)
        result[t.value] = {
            "entries": [e.model_dump() for e in entries],
            "total": total
        }
    if task_id:
        return result[task_id.value]
    return result

@app.post("/submit")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def submit_to_leaderboard(
    request: Request,
    submission: SubmitScore,
    session: Session = Depends(get_session),
    _: None = Depends(verify_api_key)
):
    rank = submit_leaderboard(
        session,
        agent_name=submission.agent_name,
        task_id=submission.task_id.value,
        score=submission.score,
        seed=submission.seed
    )
    return {"status": "submitted", "rank": rank if rank > 0 else None}

@app.get("/stats")
def get_aggregate_stats(session: Session = Depends(get_session)):
    return get_stats(session)

@app.get("/episodes/{episode_id}/replay")
def get_episode_replay(
    episode_id: str,
    session: Session = Depends(get_session),
    _: None = Depends(verify_api_key)
):
    record = get_episode(session, episode_id)
    if not record:
        raise HTTPException(status_code=404, detail="Episode not found or not yet completed")
    return {
        "episode_id": record.episode_id,
        "task_id": record.task_id,
        "scenario_hash": record.scenario_hash,
        "final_score": record.final_score,
        "history": json.loads(record.history_json or "[]"),
        "created_at": record.created_at
    }

@app.get("/episodes")
def list_episodes(
    _: None = Depends(verify_api_key),
    limit: int = Query(default=20, ge=1, le=100)
):
    episode_list = [
        {
            "episode_id": eid,
            "task_id": env.task_id,
            "step_count": env.observation.step_count,
            "done": env.done,
            "created_at": episode_timestamps.get(eid, "").isoformat() if episode_timestamps.get(eid) else ""
        }
        for eid, env in list(episodes.items())[:limit]
    ]
    return {"episodes": episode_list, "total": len(episodes)}

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(websocket)

# ── Dashboard ─────────────────────────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static", "dashboard")
if os.path.exists(static_dir):
    app.mount("/dashboard/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="dashboard-assets")

@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/{full_path:path}", include_in_schema=False)
def dashboard(full_path: str = ""):
    """Serve the React dashboard SPA (index.html for all sub-paths)."""
    # 1. Check if the requested full_path is a specific static file (e.g. logo.svg)
    if full_path:
        static_file = os.path.join(os.path.dirname(__file__), "static", "dashboard", full_path)
        if os.path.exists(static_file) and os.path.isfile(static_file):
            return FileResponse(static_file)

    # 2. Fallback to index.html for SPA routing
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard", "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Dashboard not found. Run: cd dashboard && npm run build")
    return FileResponse(html_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
