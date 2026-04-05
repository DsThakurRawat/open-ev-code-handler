import pytest
from codelens_env.scenarios import get_scenario, all_scenarios
from codelens_env.models import TaskId, Severity

# ── All 30 scenarios loadable ──────────────────────────────────────────────

def test_all_scenarios_count():
    assert len(all_scenarios()) == 30

@pytest.mark.parametrize("task_id,expected_count", [
    (TaskId.BUG_DETECTION, 10),
    (TaskId.SECURITY_AUDIT, 10),
    (TaskId.ARCHITECTURAL_REVIEW, 10),
])
def test_scenario_count_per_task(task_id, expected_count):
    scenarios = [s for s in all_scenarios() if s.task_id == task_id]
    assert len(scenarios) == expected_count

@pytest.mark.parametrize("task_id", list(TaskId))
@pytest.mark.parametrize("seed", range(10))
def test_scenario_loadable(task_id, seed):
    """Every seed for every task must return a valid scenario."""
    s = get_scenario(task_id, seed)
    assert s is not None
    assert s.hash != ""
    assert len(s.ground_truth_issues) >= 1
    assert len(s.files_changed) >= 1

@pytest.mark.parametrize("task_id", list(TaskId))
@pytest.mark.parametrize("seed", range(10))
def test_scenario_has_valid_ground_truth(task_id, seed):
    s = get_scenario(task_id, seed)
    for issue in s.ground_truth_issues:
        assert len(issue.keywords) >= 2, f"Issue {issue.id} needs >= 2 keywords"
        assert issue.filename != ""
        assert issue.line_number > 0
        assert issue.severity in list(Severity)

@pytest.mark.parametrize("task_id", list(TaskId))
@pytest.mark.parametrize("seed", range(10))
def test_scenario_has_valid_diff(task_id, seed):
    s = get_scenario(task_id, seed)
    for f in s.files_changed:
        assert "+++" in f.patch or "---" in f.patch or "@@ " in f.patch, \
            f"Scenario {s.hash}: file {f.filename} patch is not a valid diff"

def test_scenario_hashes_unique():
    hashes = [s.hash for s in all_scenarios()]
    assert len(hashes) == len(set(hashes)), "Duplicate scenario hashes found"

def test_scenario_seed_determinism():
    s1 = get_scenario(TaskId.BUG_DETECTION, 0)
    s2 = get_scenario(TaskId.BUG_DETECTION, 0)
    assert s1.hash == s2.hash, "Same seed must return same scenario"

def test_scenario_seed_wraps():
    s_seed0 = get_scenario(TaskId.BUG_DETECTION, 0)
    s_seed10 = get_scenario(TaskId.BUG_DETECTION, 10)
    assert s_seed0.hash == s_seed10.hash, "Seed 10 should wrap to same as seed 0"
