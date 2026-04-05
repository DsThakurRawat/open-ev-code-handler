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

# ─── Bug Grader Edge Cases ─────────────────────────────

def test_bug_grader_partial_match():
    """Matching some but not all issues."""
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.HIGH,
                             filename="f1", line_number=10, description="d1", keywords=["k1"]),
            GroundTruthIssue(id="2", category=Category.BUG, severity=Severity.LOW,
                             filename="f2", line_number=20, description="d2", keywords=["k2"]),
        ],
        hash="test"
    )
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="k1",
                     filename="f1", line_number=10, category=Category.BUG, severity=Severity.HIGH)
    ]
    score = grade_bug_detection(scenario, history)
    assert 0.0 < score < 1.0, f"Partial match should give intermediate score, got {score}"

def test_bug_grader_line_tolerance():
    """Issue flagged within ±3 lines should match."""
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.MEDIUM,
                             filename="f1", line_number=10, description="d", keywords=["bug"])
        ],
        hash="test"
    )
    # Flag at line 12 (within ±3)
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="bug found here",
                     filename="f1", line_number=12, category=Category.BUG, severity=Severity.MEDIUM)
    ]
    score = grade_bug_detection(scenario, history)
    assert score > 0.0, "Line within tolerance should match"

def test_bug_grader_line_out_of_tolerance():
    """Issue flagged outside ±3 lines should NOT match."""
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.MEDIUM,
                             filename="f1", line_number=10, description="d", keywords=["bug"])
        ],
        hash="test"
    )
    # Flag at line 15 (outside ±3)
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="bug found here",
                     filename="f1", line_number=15, category=Category.BUG, severity=Severity.MEDIUM)
    ]
    score = grade_bug_detection(scenario, history)
    assert score == 0.0, "Line outside tolerance should not match"

def test_bug_grader_false_positives_penalized():
    """Multiple FP flags should reduce score."""
    scenario = Scenario(
        task_id=TaskId.BUG_DETECTION, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.BUG, severity=Severity.MEDIUM,
                             filename="f1", line_number=10, description="d", keywords=["real"])
        ],
        hash="test"
    )
    history = [
        # One correct flag
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="real bug",
                     filename="f1", line_number=10, category=Category.BUG, severity=Severity.MEDIUM),
        # Three false positives
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="fp1",
                     filename="nowhere", line_number=999, category=Category.BUG, severity=Severity.LOW),
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="fp2",
                     filename="nowhere", line_number=998, category=Category.BUG, severity=Severity.LOW),
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="fp3",
                     filename="nowhere", line_number=997, category=Category.BUG, severity=Severity.LOW),
    ]
    perfect_score = 1.0
    score = grade_bug_detection(scenario, history)
    assert score < perfect_score, "FP flags should reduce score below perfect"

# ─── Security Grader Edge Cases ─────────────────────────

def test_security_grader_perfect():
    scenario = Scenario(
        task_id=TaskId.SECURITY_AUDIT, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.SECURITY, severity=Severity.CRITICAL,
                             filename="f1", line_number=10, description="d", keywords=["sql", "injection"])
        ],
        hash="test"
    )
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body="sql injection vulnerability",
                     filename="f1", line_number=10, category=Category.SECURITY, severity=Severity.CRITICAL)
    ]
    score = grade_security_audit(scenario, history)
    assert score == 1.0

def test_security_grader_empty_history():
    scenario = Scenario(
        task_id=TaskId.SECURITY_AUDIT, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.SECURITY, severity=Severity.HIGH,
                             filename="f1", line_number=5, description="d", keywords=["k1"])
        ],
        hash="test"
    )
    assert grade_security_audit(scenario, []) == 0.0

# ─── Arch Grader Edge Cases ─────────────────────────────

def test_arch_grader_correct_verdict():
    scenario = Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW, pr_title="t", pr_description="t",
        files_changed=[],
        ground_truth_issues=[
            GroundTruthIssue(id="1", category=Category.ARCHITECTURE, severity=Severity.HIGH,
                             filename="f1", line_number=10, description="d",
                             keywords=["god class", "single responsibility"],
                             required_verdict=Verdict.REQUEST_CHANGES)
        ],
        hash="test"
    )
    # Correct verdict
    body = "This is a god class violating single responsibility principle and needs major refactoring"
    history = [
        ActionRecord(action_type=ActionType.FLAG_ISSUE, body=body,
                     filename="f1", line_number=10, category=Category.ARCHITECTURE, severity=Severity.HIGH),
        ActionRecord(action_type=ActionType.REQUEST_CHANGES, body="Needs refactoring",
                     verdict=Verdict.REQUEST_CHANGES)
    ]
    score = grade_architectural_review(scenario, history)
    assert score > 0.6, f"Correct verdict should score well, got {score}"
