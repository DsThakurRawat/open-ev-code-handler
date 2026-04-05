from datetime import datetime, timezone
from typing import List, Optional, Set
from codelens_env.models import (
    TaskId, Action, Observation, StepResult, ResetResult,
    ActionType, ActionRecord, EpisodeResult, Severity, GroundTruthIssue
)
from codelens_env.scenarios import get_scenario
from codelens_env.graders.bug_grader import grade_bug_detection
from codelens_env.graders.security_grader import grade_security_audit
from codelens_env.graders.arch_grader import grade_architectural_review

class CodeLensEnv:
    MAX_NOISE_BUDGET = 5
    TASK_MAX_STEPS = {
        TaskId.BUG_DETECTION: 10,
        TaskId.SECURITY_AUDIT: 15,
        TaskId.ARCHITECTURAL_REVIEW: 20,
    }
    SEVERITY_WEIGHTS = {
        Severity.CRITICAL: 1.0,
        Severity.HIGH: 0.8,
        Severity.MEDIUM: 0.5,
        Severity.LOW: 0.2,
        Severity.INFO: 0.0,
    }

    def __init__(self):
        self.task_id: Optional[TaskId] = None
        self.seed: int = 42
        self.scenario = None
        self.step_count: int = 0
        self.noise_budget: int = self.MAX_NOISE_BUDGET
        self.history: List[ActionRecord] = []
        self.matched_issue_ids: Set[str] = set()
        self.done: bool = False
        self.terminated_reason: str = ""
        self.episode_id: str = ""

    def reset(self, task_id: TaskId, seed: int = 42) -> ResetResult:
        self.scenario = get_scenario(task_id, seed)
        self.task_id = task_id
        self.seed = seed
        self.step_count = 0
        self.noise_budget = self.MAX_NOISE_BUDGET
        self.history = []
        self.matched_issue_ids = set()
        self.done = False
        self.terminated_reason = ""
        
        obs = self._build_observation()
        return ResetResult(
            task_id=task_id,
            seed=seed,
            scenario_hash=self.scenario.hash,
            observation=obs
        )

    def step(self, action: Action) -> StepResult:
        if self.done:
            raise ValueError("Episode is already finished")

        self.step_count += 1
        reward = 0.0
        
        # Determine terminal state and reward
        if action.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES):
            self.done = True
            self.terminated_reason = "terminal_action"
            reward = 0.0 # Grader handles final score
        
        elif action.action_type == ActionType.FLAG_ISSUE:
            match = None
            for issue in self.scenario.ground_truth_issues:
                if self._is_match(action, issue):
                    match = issue
                    break
            
            if match:
                if match.id not in self.matched_issue_ids:
                    reward = self.SEVERITY_WEIGHTS.get(match.severity, 0.0)
                    self.matched_issue_ids.add(match.id)
                else:
                    # Already matched: penalty
                    reward = -0.05
                    self.noise_budget -= 1
                    if self.noise_budget <= 0:
                        self.done = True
                        self.terminated_reason = "noise_exhausted"
            else:
                # False positive: penalty
                reward = -0.05
                self.noise_budget -= 1
                if self.noise_budget <= 0:
                    self.done = True
                    self.terminated_reason = "noise_exhausted"
        
        # Max steps check
        max_steps = self.TASK_MAX_STEPS.get(self.task_id, 10)
        if not self.done and self.step_count >= max_steps:
            self.done = True
            self.terminated_reason = "max_steps"

        # Record action
        record = ActionRecord(
            action_type=action.action_type,
            body=action.body,
            filename=action.filename,
            line_number=action.line_number,
            category=action.category,
            severity=action.severity,
            verdict=action.verdict,
            reward=float(reward),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.history.append(record)

        return StepResult(
            observation=self._build_observation(),
            reward=float(reward),
            done=self.done,
            info={"terminated_reason": self.terminated_reason}
        )

    def _is_match(self, action: Action, issue: GroundTruthIssue) -> bool:
        if action.filename != issue.filename:
            return False
        if action.line_number is None:
            return False
        if abs(action.line_number - issue.line_number) > 3:
            return False
        if action.category != issue.category:
            return False
        
        body_lower = (action.body or "").lower()
        return any(kw.lower() in body_lower for kw in issue.keywords)

    def _build_observation(self) -> Observation:
        max_steps = self.TASK_MAX_STEPS.get(self.task_id, 10)
        diff = "\n".join(f.patch for f in self.scenario.files_changed)
        
        return Observation(
            task_id=self.task_id,
            scenario_hash=self.scenario.hash,
            pr_title=self.scenario.pr_title,
            pr_description=self.scenario.pr_description,
            diff=diff,
            files_changed=self.scenario.files_changed,
            step_count=self.step_count,
            max_steps=max_steps,
            noise_budget=self.noise_budget,
            max_noise_budget=self.MAX_NOISE_BUDGET,
            issues_flagged=len(self.matched_issue_ids),
            done=self.done
        )

    def get_final_result(self) -> EpisodeResult:
        if self.task_id == TaskId.BUG_DETECTION:
            final_score = grade_bug_detection(self.scenario, self.history)
        elif self.task_id == TaskId.SECURITY_AUDIT:
            final_score = grade_security_audit(self.scenario, self.history)
        else:
            final_score = grade_architectural_review(self.scenario, self.history)
            
        return EpisodeResult(
            episode_id=self.episode_id,
            task_id=self.task_id,
            scenario_hash=self.scenario.hash,
            seed=self.seed,
            final_score=round(final_score, 4),
            steps_taken=self.step_count,
            issues_found=len(self.matched_issue_ids),
            issues_total=len(self.scenario.ground_truth_issues),
            noise_penalties=self.MAX_NOISE_BUDGET - self.noise_budget,
            history=self.history,
            terminated_reason=self.terminated_reason
        )

