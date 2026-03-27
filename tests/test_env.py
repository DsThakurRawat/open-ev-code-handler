import pytest
from codereview_env.env import CodeReviewEnv
from codereview_env.models import TaskId, Action, ActionType, Category, Severity, Verdict

def test_env_reset():
    env = CodeReviewEnv()
    res = env.reset(TaskId.BUG_DETECTION, seed=0)
    assert res.task_id == TaskId.BUG_DETECTION
    assert res.seed == 0
    assert res.observation.step_count == 0
    assert res.observation.noise_budget == 5

def test_env_step_bug_detection():
    env = CodeReviewEnv()
    res = env.reset(TaskId.BUG_DETECTION, seed=1) 
    # Seed 1 selects bug_003: None dereference in auth.py
    
    # Flag the bug correctly
    action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="None dereference null check guard clause",
        filename="auth.py",
        line_number=16,
        category=Category.BUG,
        severity=Severity.HIGH
    )
    step_res = env.step(action)
    assert step_res.observation.step_count == 1
    assert step_res.reward > 0
    assert step_res.done == False

    # Terminal action
    action_term = Action(
        action_type=ActionType.APPROVE,
        body="LGTM",
        verdict=Verdict.LGTM
    )
    step_term = env.step(action_term)
    assert step_term.done == True
    
    final = env.get_final_result()
    assert final.final_score > 0

def test_env_noise_budget_exhaustion():
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=0)
    
    # Flag 5 false positives
    action_fp = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="fp",
        filename="nonexistent",
        line_number=999,
        category=Category.BUG,
        severity=Severity.LOW
    )
    
    for i in range(4):
        res = env.step(action_fp)
        assert res.done == False
        assert res.observation.noise_budget == 5 - (i + 1)
        
    res_final = env.step(action_fp)
    assert res_final.done == True
    assert res_final.observation.noise_budget == 0

def test_env_max_steps():
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=0)
    
    action_neutral = Action(
        action_type=ActionType.ASK_QUESTION,
        body="what's this?"
    )
    
    for i in range(9):
        res = env.step(action_neutral)
        assert res.done == False
        
    res_final = env.step(action_neutral)
    assert res_final.done == True
    assert res_final.observation.step_count == 10
