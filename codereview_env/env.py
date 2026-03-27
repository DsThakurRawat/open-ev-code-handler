from codereview_env.models import (
    TaskId, Action, Observation, StepResult, ResetResult,
    ActionType, ActionRecord, EpisodeResult
)
from codereview_env.scenario_bank import get_scenario
from codereview_env.graders.grader_utils import find_best_match
from codereview_env.graders.bug_grader import grade_bug_detection
from codereview_env.graders.security_grader import grade_security_audit
from codereview_env.graders.arch_grader import grade_architectural_review

class CodeReviewEnv:
    TASK_MAX_STEPS = {
        TaskId.BUG_DETECTION: 10,
        TaskId.SECURITY_AUDIT: 15,
        TaskId.ARCHITECTURAL_REVIEW: 20,
    }

    def __init__(self):
        self._state = None

    def reset(self, task_id: TaskId, seed: int = 42) -> ResetResult:
        scenario = get_scenario(task_id, seed)
        self._state = {
            "task_id": task_id,
            "seed": seed,
            "scenario": scenario,
            "step_count": 0,
            "noise_budget": 5,
            "max_steps": self.TASK_MAX_STEPS[task_id],
            "history": [],
            "running_score": 0.0,
            "done": False,
            "issues_found": set(), # Set of ground truth issue IDs
            "false_positives": []   # List of action bodies that were FPs
        }
        return ResetResult(
            observation=self._build_obs(),
            task_id=task_id,
            seed=seed,
            scenario_hash=scenario.hash
        )

    def step(self, action: Action) -> StepResult:
        if self._state is None or self._state["done"]:
            raise RuntimeError("Episode is done or not initialized. Call reset().")

        s = self._state
        s["step_count"] += 1
        
        # Record action in history
        s["history"].append(ActionRecord(
            action_type=action.action_type,
            body=action.body,
            filename=action.filename,
            line_number=action.line_number,
            severity=action.severity,
            category=action.category,
            verdict=action.verdict
        ))

        # Apply logic
        reward_delta = self._apply_action(action)
        s["running_score"] += reward_delta

        # Check termination
        s["done"] = (
            action.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES)
            or s["step_count"] >= s["max_steps"]
            or s["noise_budget"] <= 0
        )

        return StepResult(
            observation=self._build_obs(),
            reward=round(s["running_score"], 4),
            done=s["done"],
            info={
                "step": s["step_count"],
                "score": s["running_score"],
                "noise_budget": s["noise_budget"],
                "issues_found_count": len(s["issues_found"])
            }
        )

    def _build_obs(self) -> Observation:
        s = self._state
        sc = s["scenario"]
        return Observation(
            task_id=s["task_id"],
            pr_title=sc.pr_title,
            pr_description=sc.pr_description,
            diff="\n".join([f.patch for f in sc.files_changed]),
            files_changed=sc.files_changed,
            step_count=s["step_count"],
            max_steps=s["max_steps"],
            history=s["history"],
            noise_budget=s["noise_budget"]
        )

    def _apply_action(self, action: Action) -> float:
        """
        Updates the running score using specialized graders.
        """
        s = self._state
        sc = s["scenario"]
        
        if action.action_type == ActionType.FLAG_ISSUE:
            matched_gt = find_best_match(action, sc.ground_truth_issues, s["issues_found"])
            if matched_gt:
                s["issues_found"].add(matched_gt.id)
            else:
                s["noise_budget"] -= 1
                s["false_positives"].append(action.body)

        # Recalculate full score based on current history
        if s["task_id"] == TaskId.BUG_DETECTION:
            new_score = grade_bug_detection(sc, s["history"])
        elif s["task_id"] == TaskId.SECURITY_AUDIT:
            new_score = grade_security_audit(sc, s["history"])
        else:
            new_score = grade_architectural_review(sc, s["history"])
            
        reward_delta = new_score - s["running_score"]
        return reward_delta

    def get_final_result(self) -> EpisodeResult:
        s = self._state
        sc = s["scenario"]
        
        # Calculate missed issues
        all_gt_ids = {gt.id for gt in sc.ground_truth_issues}
        missed_ids = list(all_gt_ids - s["issues_found"])

        # Calculate official score via specialized graders
        if s["task_id"] == TaskId.BUG_DETECTION:
            final_score = grade_bug_detection(sc, s["history"])
        elif s["task_id"] == TaskId.SECURITY_AUDIT:
            final_score = grade_security_audit(sc, s["history"])
        else:
            final_score = grade_architectural_review(sc, s["history"])

        # Check verdict correct for Arch tasks handled by grader already, 
        # but let's keep the return schema consistent
        verdict_correct = None
        if s["task_id"] == TaskId.ARCHITECTURAL_REVIEW:
            final_action = s["history"][-1] if s["history"] else None
            if final_action and final_action.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES):
                required_verdicts = [gt.required_verdict for gt in sc.ground_truth_issues if gt.required_verdict]
                if required_verdicts:
                    verdict_correct = final_action.verdict == required_verdicts[0]

        return EpisodeResult(
            task_id=s["task_id"],
            seed=s["seed"],
            total_steps=s["step_count"],
            final_score=round(final_score, 4),
            issues_found=list(s["issues_found"]),
            issues_missed=missed_ids,
            false_positives=s["false_positives"],
            verdict_correct=verdict_correct
        )
