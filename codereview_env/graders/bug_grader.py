from typing import List
from codereview_env.models import Scenario, ActionRecord, Category, Severity, ActionType

def grade_bug_detection(scenario: Scenario, history: List[ActionRecord]) -> float:
    if not history:
        return 0.0
    
    flag_actions = [a for a in history if a.action_type == ActionType.FLAG_ISSUE]
    if not flag_actions:
        return 0.0
    
    total_issues = len(scenario.ground_truth_issues)
    if total_issues == 0:
        return 0.0
        
    matched_gt_indices = set()
    used_action_indices = set()
    issue_scores = []
    
    for i, truth in enumerate(scenario.ground_truth_issues):
        if truth.category != Category.BUG:
            continue
            
        # Try to find a matching action for this ground truth issue
        best_match_idx = -1
        for j, action in enumerate(flag_actions):
            if j in used_action_indices:
                continue
                
            # Match criteria: filename, line +- 3, category BUG, >= 1 keyword
            if (action.filename == truth.filename and
                action.line_number is not None and
                abs(action.line_number - truth.line_number) <= 3 and
                action.category == Category.BUG):
                
                body_lower = (action.body or "").lower()
                if any(kw.lower() in body_lower for kw in truth.keywords):
                    best_match_idx = j
                    break
        
        if best_match_idx != -1:
            action = flag_actions[best_match_idx]
            used_action_indices.add(best_match_idx)
            matched_gt_indices.add(i)
            
            # Calculate issue score
            sev_diff = abs(Severity.ordinal(truth.severity) - Severity.ordinal(action.severity))
            sev_score = max(0.0, 1.0 - sev_diff * 0.3)
            
            body_lower = (action.body or "").lower()
            match_count = sum(1 for kw in truth.keywords if kw.lower() in body_lower)
            kw_score = match_count / len(truth.keywords)
            
            issue_score = 0.5 * kw_score + 0.5 * sev_score
            issue_scores.append(issue_score)
            
    coverage = len(matched_gt_indices) / total_issues
    avg_issue_score = sum(issue_scores) / len(issue_scores) if issue_scores else 0.0
    
    total_flags = len(flag_actions)
    unmatched_flags = total_flags - len(used_action_indices)
    precision_penalty = unmatched_flags / max(1, total_flags)
    
    final_score = 0.4 * coverage + 0.6 * avg_issue_score - 0.1 * precision_penalty
    return float(max(0.0, min(1.0, final_score)))

