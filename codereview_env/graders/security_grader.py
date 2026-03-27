from typing import List
from codereview_env.models import Scenario, ActionRecord, Category, Severity
from codereview_env.graders.grader_utils import find_best_match, keyword_overlap

def severity_to_int(sev: Severity) -> int:
    mapping = {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4
    }
    return mapping.get(sev, 0)

def grade_security_audit(scenario: Scenario, history: List[ActionRecord]) -> float:
    """Grade security audit: 0.7 * correct_severity + 0.3 * keyword_accuracy."""
    flagged_actions = [r for r in history if r.category == Category.SECURITY]
    if not scenario.ground_truth_issues:
        return 1.0 if not flagged_actions else 0.0
        
    total_score = 0.0
    already_matched = set()
    
    for action in flagged_actions:
        match = find_best_match(action, scenario.ground_truth_issues, already_matched)
        if match:
            # Correct Severity: 1.0 if match, else penalty per level
            sev_diff = abs(severity_to_int(action.severity) - severity_to_int(match.severity))
            sev_score = max(0.0, 1.0 - (sev_diff * 0.3))
            
            # Keyword Accuracy
            kw_score = keyword_overlap(action.body, match.keywords)
            
            total_score += 0.7 * sev_score + 0.3 * kw_score
            already_matched.add(match.id)
            
    # Normalize by number of GT issues
    return round(min(1.0, total_score / len(scenario.ground_truth_issues)), 4) if scenario.ground_truth_issues else 1.0
