import pytest
from fastapi.testclient import TestClient
from app import app
from codelens_env.models import TaskId, ActionType, Category, Severity, Verdict

def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["env_ready"] is True

def test_api_workflow(client):
    
    # 1. Reset
    reset_resp = client.post("/reset", json={"task_id": "bug_detection", "seed": 1})
    assert reset_resp.status_code == 200
    data = reset_resp.json()
    episode_id = data["episode_id"]
    assert "observation" in data["result"]

    # 2. Step
    action = {
        "action_type": "comment",
        "body": "Starting review",
    }
    step_resp = client.post(f"/step/{episode_id}", json=action)
    assert step_resp.status_code == 200
    assert "observation" in step_resp.json()

    # 3. Get Result
    result_resp = client.get(f"/result/{episode_id}")
    assert result_resp.status_code == 200
    assert result_resp.json()["final_score"] >= 0

def test_api_leaderboard(client):
    # Submit a score
    sub = {
        "agent_name": "test_agent",
        "task_id": "bug_detection",
        "score": 0.95,
        "seed": 42
    }
    resp = client.post("/submit", json=sub)
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"
    
    # Check leaderboard
    lb_resp = client.get("/leaderboard")
    assert lb_resp.status_code == 200
    lb_data = lb_resp.json()
    bug_entries = lb_data["bug_detection"]["entries"]
    assert len(bug_entries) > 0
    assert bug_entries[0]["agent_name"] == "test_agent"

def test_api_invalid_episode(client):
    response = client.post("/step/nonexistent-id", json={
        "action_type": "comment",
        "body": "hello"
    })
    assert response.status_code == 404

def test_api_health_fields(client):
    resp = client.get("/health")
    data = resp.json()
    assert "active_episodes" in data
    assert "auth_enabled" in data
    assert "env" in data

def test_api_reset_invalid_task(client):
    resp = client.post("/reset", json={"task_id": "invalid_task", "seed": 0})
    assert resp.status_code == 422

def test_api_step_invalid_action_type(client):
    reset_resp = client.post("/reset", json={"task_id": "bug_detection", "seed": 0})
    episode_id = reset_resp.json()["episode_id"]
    resp = client.post(f"/step/{episode_id}", json={"action_type": "not_valid", "body": "x"})
    assert resp.status_code == 422

def test_api_result_after_completion(client):
    """Result endpoint should return persisted data for completed episodes."""
    reset_resp = client.post("/reset", json={"task_id": "bug_detection", "seed": 0})
    episode_id = reset_resp.json()["episode_id"]
    # Complete the episode
    client.post(f"/step/{episode_id}", json={
        "action_type": "approve", "body": "LGTM", "verdict": "lgtm"
    })
    # Result must be available
    result_resp = client.get(f"/result/{episode_id}")
    assert result_resp.status_code == 200
    assert result_resp.json()["final_score"] >= 0

def test_api_stats_endpoint(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    assert "total_episodes" in resp.json()

@pytest.mark.parametrize("task_id", ["bug_detection", "security_audit", "architectural_review"])
def test_api_full_workflow_all_tasks(client, task_id):
    reset = client.post("/reset", json={"task_id": task_id, "seed": 1})
    assert reset.status_code == 200
    episode_id = reset.json()["episode_id"]
    
    step = client.post(f"/step/{episode_id}", json={
        "action_type": "approve", "body": "LGTM", "verdict": "lgtm"
    })
    assert step.status_code == 200
    assert step.json()["done"] is True

def test_api_leaderboard_pagination(client):
    # Submit 3 entries
    for i, score in enumerate([0.9, 0.7, 0.5]):
        client.post("/submit", json={
            "agent_name": f"agent_{i}", "task_id": "bug_detection",
            "score": score, "seed": i
        })
    
    # Test limit
    resp = client.get("/leaderboard?task_id=bug_detection&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entries"]) == 2
    assert data["total"] >= 3
    
    # Test ordering (best first)
    assert data["entries"][0]["score"] >= data["entries"][1]["score"]
