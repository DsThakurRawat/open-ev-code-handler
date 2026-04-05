from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, model_validator

class TaskId(str, Enum):
    BUG_DETECTION = "bug_detection"
    SECURITY_AUDIT = "security_audit"
    ARCHITECTURAL_REVIEW = "architectural_review"

class ActionType(str, Enum):
    FLAG_ISSUE = "flag_issue"
    COMMENT = "comment"
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    ASK_QUESTION = "ask_question"

class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    STYLE = "style"
    PERFORMANCE = "performance"

class Severity(str, Enum):
    CRITICAL = "critical"    # ordinal 4
    HIGH = "high"            # ordinal 3
    MEDIUM = "medium"        # ordinal 2
    LOW = "low"              # ordinal 1
    INFO = "info"            # ordinal 0

    @classmethod
    def ordinal(cls, sev: "Severity") -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[sev.value]

class Verdict(str, Enum):
    LGTM = "lgtm"
    REQUEST_CHANGES = "request_changes"
    NEEDS_DISCUSSION = "needs_discussion"

class FileChanged(BaseModel):
    filename: str
    language: str
    patch: str                          # unified diff of this file
    additions: int = 0
    deletions: int = 0

class GroundTruthIssue(BaseModel):
    id: str
    category: Category
    severity: Severity
    filename: str
    line_number: int
    description: str
    keywords: List[str]                 # at least 2 keywords the agent body must contain
    required_verdict: Optional[Verdict] = None   # if set, terminal verdict is graded

class Scenario(BaseModel):
    task_id: TaskId
    pr_title: str
    pr_description: str
    files_changed: List[FileChanged]
    ground_truth_issues: List[GroundTruthIssue]
    hash: str                           # deterministic identifier, e.g. "bug_001"
    difficulty: str = "medium"          # easy | medium | hard
    tags: List[str] = []

class Action(BaseModel):
    action_type: ActionType
    body: str = ""
    filename: Optional[str] = None
    line_number: Optional[int] = None
    category: Optional[Category] = None
    severity: Optional[Severity] = None
    verdict: Optional[Verdict] = None

    @model_validator(mode="after")
    def validate_action_fields(self) -> "Action":
        if self.action_type == ActionType.FLAG_ISSUE:
            if not self.body or not self.filename or self.line_number is None:
                raise ValueError("flag_issue requires body, filename, and line_number")
            if not self.category or not self.severity:
                raise ValueError("flag_issue requires category and severity")
        elif self.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES):
            if not self.verdict:
                raise ValueError(f"{self.action_type.value} action requires a verdict")
            if not self.body:
                raise ValueError(f"{self.action_type.value} action requires a body summary")
        return self

class ActionRecord(BaseModel):
    """Immutable record of a step taken — stored in episode history."""
    action_type: ActionType
    body: str = ""
    filename: Optional[str] = None
    line_number: Optional[int] = None
    category: Optional[Category] = None
    severity: Optional[Severity] = None
    verdict: Optional[Verdict] = None
    reward: float = 0.0
    timestamp: str = ""     # ISO format, set by env

class Observation(BaseModel):
    task_id: TaskId
    scenario_hash: str
    pr_title: str
    pr_description: str
    diff: str                           # full unified diff (all files concatenated)
    files_changed: List[FileChanged]
    step_count: int
    max_steps: int
    noise_budget: int
    max_noise_budget: int = 5
    issues_flagged: int = 0
    done: bool = False

class ResetResult(BaseModel):
    task_id: TaskId
    seed: int
    scenario_hash: str
    observation: Observation

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict = {}

class EpisodeResult(BaseModel):
    episode_id: str = ""
    task_id: TaskId
    scenario_hash: str
    seed: int
    final_score: float
    steps_taken: int
    issues_found: int
    issues_total: int
    noise_penalties: int
    history: List[ActionRecord] = []
    terminated_reason: str = ""         # "terminal_action"|"max_steps"|"noise_exhausted"
