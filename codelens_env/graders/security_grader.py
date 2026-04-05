from typing import List
from codelens_env.models import Scenario, ActionRecord, Category, Severity, ActionType

def grade_security_audit(scenario: Scenario, history: List[ActionRecord]) -> float:
    if not history:
        return 0.0
        
    flag_actions = [a for a in history if a.action_type == ActionType.FLAG_ISSUE]
    if not flag_actions:
        return 0.0
        
    matched_issue_scores = []
    used_action_indices = set()
    
    for truth in scenario.ground_truth_issues:
        if truth.category != Category.SECURITY:
            continue
            
        best_match_idx = -1
        for j, action in enumerate(flag_actions):
            if j in used_action_indices:
                continue
                
            # Match criteria: filename, line +- 3, category SECURITY, >= 1 keyword
            if (action.filename == truth.filename and
                action.line_number is not None and
                abs(action.line_number - truth.line_number) <= 3 and
                action.category == Category.SECURITY):
                
                body_lower = (action.body or "").lower()
                if any(kw.lower() in body_lower for kw in truth.keywords):
                    best_match_idx = j
                    break
        
        if best_match_idx != -1:
            action = flag_actions[best_match_idx]
            used_action_indices.add(best_match_idx)
            
            # Calculate issue score
            sev_diff = abs(Severity.ordinal(truth.severity) - Severity.ordinal(action.severity))
            sev_score = max(0.0, 1.0 - sev_diff * 0.3)
            
            body_lower = (action.body or "").lower()
            match_count = sum(1 for kw in truth.keywords if kw.lower() in body_lower)
            kw_threshold = len(truth.keywords) if truth.keywords else 1
            kw_score = match_count / kw_threshold
            
            issue_score = 0.7 * sev_score + 0.3 * kw_score
            matched_issue_scores.append(issue_score)
            
    if not matched_issue_scores:
        return 0.0
        
    final_score = sum(matched_issue_scores) / len(matched_issue_scores)
    return float(round(max(0.0, min(1.0, final_score)), 4))

