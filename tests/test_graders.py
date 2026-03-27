from codereview_env.models import Scenario, ActionRecord, Category, Severity, TaskId, GroundTruthIssue, ActionType, Verdict
from codereview_env.graders.bug_grader import grade_bug_detection
from codereview_env.graders.security_grader import grade_security_audit
from codereview_env.graders.arch_grader import grade_architectural_review

def test_bug_grader_perfect():
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="test", pr_description="test",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.MEDIUM, filename="f1", line_number=10, description="d1", keywords=["k1", "k2"])
        ],
        hash="h1"
    )
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="found k1 k2", filename="f1", line_number=10, category=Category.BUG, severity=Severity.MEDIUM)
    ]
    score = grade_bug_detection(scenario, history)
    assert score == 1.0

def test_bug_grader_none():
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="test", pr_description="test",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.MEDIUM, filename="f1", line_number=10, description="d1", keywords=["k1", "k2"])
        ],
        hash="h1"
    )
    history = []
    score = grade_bug_detection(scenario, history)
    assert score == 0.0

def test_security_grader_severity_mismatch():
    scenario = Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="test", pr_description="test",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.SECURITY, severity=Severity.CRITICAL, filename="f1", line_number=10, description="d1", keywords=["k1"])
        ],
        hash="h1"
    )
    # Low severity flagged when it was critical
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="k1", filename="f1", line_number=10, category=Category.SECURITY, severity=Severity.LOW)
    ]
    score = grade_security_audit(scenario, history)
    # sev_diff = 3, sev_score = max(0, 1 - 3*0.3) = 0.1
    # threshold = max(4, 1*0.6) = 4. kw_score = 1/4 = 0.25
    # total_score = 0.7 * 0.1 + 0.3 * 0.25 = 0.07 + 0.075 = 0.145
    assert score == 0.145

def test_arch_grader_verdict():
    scenario = Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="test", pr_description="test",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.ARCHITECTURE, severity=Severity.HIGH, filename="f1", line_number=10, description="d1", keywords=["k1"], required_verdict=Verdict.REQUEST_CHANGES)
        ],
        hash="h1"
    )
    # Flagged issue but approved (wrong verdict)
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="k1", filename="f1", line_number=10, category=Category.ARCHITECTURE, severity=Severity.HIGH),
        ActionRecord(action_type=ActionType.APPROVE, body="lgtm", verdict=Verdict.LGTM)
    ]
    score = grade_architectural_review(scenario, history)
    # issue_score = 1.0, verdict_score = 0.0, quality_score = 0.0
    # score = 0.6 * 1.0 + 0.2 * 0.0 + 0.0 = 0.6
    assert score == 0.6
