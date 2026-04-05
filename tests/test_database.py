from sqlmodel import Session
from codelens_env.database import save_episode, get_episode, submit_leaderboard, get_leaderboard_db, get_stats
from codelens_env.models import EpisodeResult, TaskId, ActionRecord, ActionType

def make_result(episode_id="test-ep-1", score=0.85):
    return EpisodeResult(
        episode_id=episode_id,
        task_id=TaskId.BUG_DETECTION,
        scenario_hash="bug_001",
        seed=0,
        final_score=score,
        steps_taken=3,
        issues_found=1,
        issues_total=1,
        noise_penalties=0,
        terminated_reason="terminal_action",
        history=[ActionRecord(action_type=ActionType.APPROVE, body="LGTM")]
    )

def test_save_and_get_episode(session):
    result = make_result()
    save_episode(session, result)
    record = get_episode(session, "test-ep-1")
    assert record is not None
    assert record.final_score == 0.85
    assert record.scenario_hash == "bug_001"

def test_get_nonexistent_episode(session):
    record = get_episode(session, "does-not-exist")
    assert record is None

def test_episode_history_serialized(session):
    result = make_result()
    save_episode(session, result)
    record = get_episode(session, result.episode_id)
    import json
    history = json.loads(record.history_json)
    assert len(history) == 1
    assert history[0]["action_type"] == "approve"

def test_leaderboard_submit_and_rank(session):
    rank = submit_leaderboard(session, "agent_a", "bug_detection", 0.9, 0)
    assert rank == 1
    rank2 = submit_leaderboard(session, "agent_b", "bug_detection", 0.7, 1)
    assert rank2 == 2

def test_leaderboard_ordering(session):
    submit_leaderboard(session, "low", "security_audit", 0.3, 0)
    submit_leaderboard(session, "high", "security_audit", 0.95, 1)
    submit_leaderboard(session, "mid", "security_audit", 0.6, 2)
    entries, total = get_leaderboard_db(session, "security_audit")
    assert total == 3
    assert entries[0].agent_name == "high"
    assert entries[0].score == 0.95

def test_get_stats_empty(session):
    stats = get_stats(session)
    assert stats["total_episodes"] == 0

def test_get_stats_populated(session):
    save_episode(session, make_result("ep1", 0.9))
    save_episode(session, make_result("ep2", 0.5))
    stats = get_stats(session)
    assert stats["total_episodes"] == 2
    assert abs(stats["avg_score"] - 0.7) < 0.001
