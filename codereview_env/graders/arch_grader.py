from typing import List
from codereview_env.models import Scenario, ActionRecord, Category, ActionType, Verdict
from codereview_env.graders.grader_utils import find_best_match

def grade_architectural_review(scenario: Scenario, history: List[ActionRecord]) -> float:
    """Grade architectural review: 0.6 * issue_score + 0.2 * verdict_score + 0.2 * quality_score."""
    critical_issues = scenario.ground_truth_issues
    flagged_actions = [r for r in history if r.category == Category.ARCHITECTURE]
    
    # 1. Issue Detection (0.6)
    found_count = 0
    already_matched = set()
    quality_bonus = 0.0
    
    for action in flagged_actions:
        match = find_best_match(action, critical_issues, already_matched)
        if match:
            found_count += 1
            already_matched.add(match.id)
            # Quality: + bonus if body is descriptive (> 80 chars)
            if len(action.body) > 80:
                quality_bonus += 0.05
    
    issue_score = (found_count / len(critical_issues)) if critical_issues else 1.0
    
    # 2. Verdict Correctness (0.2)
    verdict_score = 0.0
    final_action = history[-1] if history else None
    if final_action and final_action.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES):
        # Check against the first required verdict in GT
        required_verdicts = [gt.required_verdict for gt in critical_issues if gt.required_verdict]
        if required_verdicts and final_action.verdict == required_verdicts[0]:
            verdict_score = 1.0
        elif not required_verdicts and final_action.verdict == Verdict.LGTM:
            verdict_score = 1.0

    # 3. Final weighted calculation
    score = 0.6 * issue_score + 0.2 * verdict_score + min(0.2, quality_bonus)
    return round(min(1.0, score), 4)
