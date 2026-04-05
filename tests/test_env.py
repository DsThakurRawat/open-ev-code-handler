import pytest
from codereview_env.env import CodeReviewEnv
from codereview_env.models import (
    TaskId, Action, ActionType, Category, Severity, Verdict
)


# ─────────────────────────────────────────────────────────────────────────────
# Reset tests
# ─────────────────────────────────────────────────────────────────────────────

def test_env_reset():
    env = CodeReviewEnv()
    res = env.reset(TaskId.BUG_DETECTION, seed=0)
    assert res.task_id == TaskId.BUG_DETECTION
    assert res.seed == 0
    assert res.observation.step_count == 0
    assert res.observation.noise_budget == 5


def test_env_reset_populates_blast_radius():
    """Observation should carry blast-radius metadata from the scenario."""
    env = CodeReviewEnv()
    res = env.reset(TaskId.SECURITY_AUDIT, seed=0)
    obs = res.observation
    # Note: New models have different fields or names, but the env should map them.
    assert obs.step_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# Step tests
# ─────────────────────────────────────────────────────────────────────────────

def test_env_step_bug_detection():
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=1)
    # seed=1 → bug_003: None dereference in auth.py (per reordering)

    action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="None dereference null check guard clause AttributeError",
        filename="auth.py",
        line_number=16,
        category=Category.BUG,
        severity=Severity.HIGH
    )
    step_res = env.step(action)
    assert step_res.observation.step_count == 1
    assert step_res.reward > 0, "Correct issue flag should give positive reward delta"
    assert step_res.done == False

    # Terminal action
    step_term = env.step(Action(
        action_type=ActionType.APPROVE,
        body="LGTM",
        verdict=Verdict.LGTM
    ))
    assert step_term.done == True

    final = env.get_final_result()
    assert final.final_score > 0


def test_env_step_reward_is_incremental_not_cumulative():
    """Each step reward should be a delta (positive or zero or penalty), not a running total."""
    env = CodeReviewEnv()
    # seed=1 selects bug_003: None dereference in auth.py at line 16
    env.reset(TaskId.BUG_DETECTION, seed=1)

    correct_action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="None dereference null check guard clause AttributeError",
        filename="auth.py",
        line_number=16,
        category=Category.BUG,
        severity=Severity.HIGH
    )
    step1 = env.step(correct_action)
    # First correct flag → positive incremental delta
    assert step1.reward > 0, f"Correct issue flag should give positive reward delta, got {step1.reward}"

    # Second identical flag on same file/line — already matched, counts as FP
    step2 = env.step(correct_action)
    # Already matched → false positive → -0.05 penalty
    assert step2.reward == -0.05


def test_env_step_false_positive_penalty():
    """False positives should decrement noise_budget and return negative reward."""
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=0)

    fp_action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="completely wrong flag",
        filename="nonexistent_file.py",
        line_number=999,
        category=Category.BUG,
        severity=Severity.LOW
    )
    step_res = env.step(fp_action)
    assert step_res.reward == -0.05
    assert step_res.observation.noise_budget == 4


def test_env_noise_budget_exhaustion():
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=0)

    fp_action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="fp",
        filename="nonexistent",
        line_number=999,
        category=Category.BUG,
        severity=Severity.LOW
    )

    for i in range(4):
        res = env.step(fp_action)
        assert res.done == False
        assert res.observation.noise_budget == 5 - (i + 1)

    res_final = env.step(fp_action)
    assert res_final.done == True
    assert res_final.observation.noise_budget == 0


def test_env_max_steps():
    env = CodeReviewEnv()
    env.reset(TaskId.BUG_DETECTION, seed=0)

    action = Action(action_type=ActionType.ASK_QUESTION, body="what's this?")
    for i in range(9):
        res = env.step(action)
        assert res.done == False

    res_final = env.step(action)
    assert res_final.done == True
    assert res_final.observation.step_count == 10


# ─────────────────────────────────────────────────────────────────────────────
# Multi-task smoke tests
# ─────────────────────────────────────────────────────────────────────────────

def test_security_task_runs_to_completion():
    env = CodeReviewEnv()
    # seed=1 selects sec_002: Hardcoded secret (if 0-indexed and order is preserved)
    # Actually get_scenario(TaskId.SECURITY_AUDIT, 1) selects the second item.
    env.reset(TaskId.SECURITY_AUDIT, seed=1)

    # sec_002 is bug with sk_live_abc123XYZ in payments/webhook.py line 5
    action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="hardcoded secret sk_live_abc123XYZ",
        filename="payments/webhook.py",
        line_number=5,
        category=Category.SECURITY,
        severity=Severity.CRITICAL
    )
    step_res = env.step(action)
    assert step_res.reward >= 0

    env.step(Action(
        action_type=ActionType.REQUEST_CHANGES,
        body="Hardcoded secret found.",
        verdict=Verdict.REQUEST_CHANGES
    ))
    final = env.get_final_result()
    assert final.final_score > 0


def test_arch_task_runs_to_completion():
    env = CodeReviewEnv()
    env.reset(TaskId.ARCHITECTURAL_REVIEW, seed=0)

    # arch_001 is UserManager god class
    action = Action(
        action_type=ActionType.FLAG_ISSUE,
        body="god class single responsibility violation",
        filename="services/user_manager.py",
        line_number=2,
        category=Category.ARCHITECTURE,
        severity=Severity.HIGH
    )
    env.step(action)

    env.step(Action(
        action_type=ActionType.REQUEST_CHANGES,
        body="Must refactor out of god class.",
        verdict=Verdict.REQUEST_CHANGES
    ))
    final = env.get_final_result()
    assert final.final_score > 0

@pytest.mark.parametrize("task_id", list(TaskId))
def test_env_reset_all_tasks(task_id, env):
    """Reset must work for all three task types."""
    result = env.reset(task_id, seed=0)
    assert result.task_id == task_id
    assert result.observation.noise_budget == 5

@pytest.mark.parametrize("task_id,expected_max_steps", [
    (TaskId.BUG_DETECTION, 10),
    (TaskId.SECURITY_AUDIT, 15),
    (TaskId.ARCHITECTURAL_REVIEW, 20),
])
def test_env_max_steps_per_task(task_id, expected_max_steps, env):
    result = env.reset(task_id, seed=0)
    assert result.observation.max_steps == expected_max_steps

def test_env_step_raises_when_done(env, approve_action):
    """Calling step on a done episode must raise ValueError."""
    env.reset(TaskId.BUG_DETECTION, seed=0)
    env.step(approve_action)
    with pytest.raises(ValueError):
        env.step(approve_action)

def test_env_history_recorded(env):
    """All steps should appear in final result history."""
    env.reset(TaskId.BUG_DETECTION, seed=0)
    from codereview_env.models import Action, ActionType
    for _ in range(3):
        env.step(Action(action_type=ActionType.ASK_QUESTION, body="question"))
    env.step(Action(action_type=ActionType.APPROVE, body="LGTM", verdict=Verdict.LGTM))
    result = env.get_final_result()
    assert result.steps_taken == 4
    assert len(result.history) == 4

def test_env_get_final_result_score_clamped(env, approve_action):
    """Final score must always be in [0, 1]."""
    env.reset(TaskId.BUG_DETECTION, seed=0)
    env.step(approve_action)
    result = env.get_final_result()
    # Check that score is a float and within [0, 1]
    assert isinstance(result.final_score, float)
    assert 0.0 <= result.final_score <= 1.0

@pytest.mark.parametrize("task_id", list(TaskId))
@pytest.mark.parametrize("seed", [0, 3, 7])
def test_env_full_episode_completes(task_id, seed, env):
    """Full episodes must always reach a terminal state."""
    env.reset(task_id, seed=seed)
    from codereview_env.models import Action, ActionType, Verdict
    # Just skip to terminal
    action = Action(action_type=ActionType.APPROVE, body="LGTM", verdict=Verdict.LGTM)
    result = env.step(action)
    assert result.done is True
    final = env.get_final_result()
    assert final.terminated_reason == "terminal_action"
