import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from codereview_env.models import (
    TaskId, Action, ResetResult, StepResult, EpisodeResult
)
from codereview_env.env import CodeReviewEnv

app = FastAPI(
    title="AgentOrg CodeReview OpenEnv API",
    description=(
        "AI Senior Code Reviewer evaluation environment. "
        "Trains agents to detect bugs, security vulnerabilities, and architectural issues "
        "in realistic Python PRs grounded in real-world incident patterns."
    ),
    version="1.0.0",
)

# Simple in-memory storage for active episodes
episodes: Dict[str, CodeReviewEnv] = {}


class ResetRequest(BaseModel):
    task_id: TaskId
    seed:    int = 42


class ResetResponse(BaseModel):
    episode_id: str
    result:     ResetResult


# In-memory leaderboard
leaderboard: Dict[TaskId, list] = {
    TaskId.BUG_DETECTION:        [],
    TaskId.SECURITY_AUDIT:       [],
    TaskId.ARCHITECTURAL_REVIEW: []
}


class SubmitScore(BaseModel):
    agent_name: str
    task_id:    TaskId
    score:      float
    seed:       int


# ── WebSocket clients ─────────────────────────────────────────────────────────
clients = set()


async def broadcast_event(data: dict):
    from fastapi.encoders import jsonable_encoder
    import json
    message = json.dumps(jsonable_encoder(data))
    dead = set()
    for client in clients:
        try:
            await client.send_text(message)
        except Exception:
            dead.add(client)
    clients.difference_update(dead)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status":    "ok",
        "version":   "1.0.0",
        "env_ready": True,
        "active_episodes": len(episodes),
    }


@app.post("/reset", response_model=ResetResponse)
def reset_env(req: ResetRequest):
    episode_id = str(uuid.uuid4())
    env        = CodeReviewEnv()
    result     = env.reset(req.task_id, req.seed)
    episodes[episode_id] = env
    return ResetResponse(episode_id=episode_id, result=result)


@app.post("/step/{episode_id}", response_model=StepResult)
async def step_env(episode_id: str, action: Action):
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")

    env = episodes[episode_id]
    try:
        result = env.step(action)
        await broadcast_event({"episode_id": episode_id, "type": "step", "reward": result.reward})
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/result/{episode_id}", response_model=EpisodeResult)
def get_result(episode_id: str):
    if episode_id not in episodes:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episodes[episode_id].get_final_result()


@app.get("/leaderboard")
def get_leaderboard():
    return leaderboard


@app.post("/submit")
def submit_to_leaderboard(submission: SubmitScore):
    entries   = leaderboard.get(submission.task_id, [])
    new_entry = submission.model_dump()
    entries.append(new_entry)
    entries.sort(key=lambda x: x["score"], reverse=True)
    rank = entries.index(new_entry) + 1   # capture rank before slicing
    leaderboard[submission.task_id] = entries[:5]
    return {"status": "submitted", "rank": rank if rank <= 5 else None}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
