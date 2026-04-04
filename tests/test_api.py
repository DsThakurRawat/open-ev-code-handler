import pytest
from fastapi.testclient import TestClient
from app import app
from codereview_env.models import TaskId, ActionType, Category, Severity, Verdict

def test_api_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["env_ready"] is True

def test_api_workflow():
    client = TestClient(app)
    
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

def test_api_leaderboard():
    client = TestClient(app)
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

def test_api_invalid_episode():
    client = TestClient(app)
    response = client.post("/step/nonexistent-id", json={
        "action_type": "comment",
        "body": "hello"
    })
    assert response.status_code == 404
