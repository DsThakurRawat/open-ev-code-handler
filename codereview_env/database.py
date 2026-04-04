from pathlib import Path
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List, Tuple
import json
from codereview_env.config import get_settings
from codereview_env.models import EpisodeResult, TaskId

def get_engine():
    settings = get_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{settings.db_path}",
        echo=settings.db_echo,
        connect_args={"check_same_thread": False}
    )

def create_db_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session

class EpisodeRecord(SQLModel, table=True):
    __tablename__ = "episodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    episode_id: str = Field(index=True, unique=True)
    task_id: str
    scenario_hash: str
    seed: int
    final_score: float
    steps_taken: int
    issues_found: int
    issues_total: int
    noise_penalties: int
    terminated_reason: str
    history_json: str = ""      # JSON-serialized list of ActionRecord dicts
    created_at: str = ""        # ISO datetime
    agent_name: str = ""        # optional, set via /submit

class LeaderboardRecord(SQLModel, table=True):
    __tablename__ = "leaderboard"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_name: str
    task_id: str = Field(index=True)
    score: float
    seed: int
    episode_id: str = ""
    submitted_at: str = ""      # ISO datetime

def save_episode(session: Session, result: EpisodeResult) -> EpisodeRecord:
    """Persist a completed episode result."""
    from datetime import datetime, timezone
    record = EpisodeRecord(
        episode_id=result.episode_id,
        task_id=result.task_id.value,
        scenario_hash=result.scenario_hash,
        seed=result.seed,
        final_score=result.final_score,
        steps_taken=result.steps_taken,
        issues_found=result.issues_found,
        issues_total=result.issues_total,
        noise_penalties=result.noise_penalties,
        terminated_reason=result.terminated_reason,
        history_json=json.dumps([r.model_dump() for r in result.history]),
        created_at=datetime.now(timezone.utc).isoformat()
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

def get_episode(session: Session, episode_id: str) -> Optional[EpisodeRecord]:
    return session.exec(select(EpisodeRecord).where(EpisodeRecord.episode_id == episode_id)).first()

def get_leaderboard_db(session: Session, task_id: str, limit: int = 10, offset: int = 0) -> Tuple[List[LeaderboardRecord], int]:
    results = session.exec(
        select(LeaderboardRecord)
        .where(LeaderboardRecord.task_id == task_id)
        .order_by(LeaderboardRecord.score.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    # Fixed: session.exec(select(LeaderboardRecord).where(LeaderboardRecord.task_id == task_id)).all() is not efficient but the snippet used it.
    # To get count specifically:
    from sqlmodel import func
    total = session.exec(
        select(func.count()).select_from(LeaderboardRecord).where(LeaderboardRecord.task_id == task_id)
    ).one()
    return list(results), total

def submit_leaderboard(session: Session, agent_name: str, task_id: str, score: float, seed: int, episode_id: str = "") -> int:
    """Add entry to leaderboard. Returns rank (1-indexed)."""
    from datetime import datetime, timezone
    record = LeaderboardRecord(
        agent_name=agent_name,
        task_id=task_id,
        score=score,
        seed=seed,
        episode_id=episode_id,
        submitted_at=datetime.now(timezone.utc).isoformat()
    )
    session.add(record)
    session.commit()
    # Calculate rank
    rank_result = session.exec(
        select(LeaderboardRecord)
        .where(LeaderboardRecord.task_id == task_id)
        .order_by(LeaderboardRecord.score.desc())
    ).all()
    for i, r in enumerate(rank_result):
        if r.id == record.id:
            return i + 1
    return -1

def get_stats(session: Session) -> dict:
    """Return aggregate statistics about all recorded episodes."""
    all_episodes = session.exec(select(EpisodeRecord)).all()
    if not all_episodes:
        return {"total_episodes": 0, "avg_score": 0.0, "by_task": {}}
    
    from collections import defaultdict
    by_task = defaultdict(list)
    for ep in all_episodes:
        by_task[ep.task_id].append(ep.final_score)
    
    return {
        "total_episodes": len(all_episodes),
        "avg_score": sum(ep.final_score for ep in all_episodes) / len(all_episodes),
        "by_task": {
            task: {
                "count": len(scores),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "best_score": max(scores) if scores else 0,
            }
            for task, scores in by_task.items()
        }
    }
