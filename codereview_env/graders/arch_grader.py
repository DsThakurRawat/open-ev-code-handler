from typing import List
from codereview_env.models import Scenario, ActionRecord, Category, ActionType, Verdict

def grade_architectural_review(scenario: Scenario, history: List[ActionRecord]) -> float:
    if not history:
        return 0.0
        
    flag_actions = [a for a in history if a.action_type == ActionType.FLAG_ISSUE]
    
    total_issues = len(scenario.ground_truth_issues)
    if total_issues == 0:
        return 0.0
        
    # 1. Match issues and calculate issue_score_avg
    matched_gt_indices = set()
    for i, truth in enumerate(scenario.ground_truth_issues):
        if truth.category != Category.ARCHITECTURE:
            continue
            
        for action in flag_actions:
            # Match criteria: filename, line +- 5, category ARCHITECTURE, keyword match
            if (action.filename == truth.filename and
                action.line_number is not None and
                abs(action.line_number - truth.line_number) <= 5 and
                action.category == Category.ARCHITECTURE):
                
                body_lower = (action.body or "").lower()
                if any(kw.lower() in body_lower for kw in truth.keywords):
                    matched_gt_indices.add(i)
                    break
                    
    issue_score_avg = len(matched_gt_indices) / total_issues
    
    # 2. Verdict Grading
    terminal_action = None
    for action in history:
        if action.action_type in (ActionType.APPROVE, ActionType.REQUEST_CHANGES):
            terminal_action = action
            break # Use the first terminal action
            
    verdict_scores = []
    for truth in scenario.ground_truth_issues:
        if truth.required_verdict:
            score = 1.0 if (terminal_action and terminal_action.verdict == truth.required_verdict) else 0.0
            verdict_scores.append(score)
            
    verdict_avg = sum(verdict_scores) / len(verdict_scores) if verdict_scores else 0.0
    
    # 3. Quality Score
    max_body_len = 0
    for action in flag_actions:
        max_body_len = max(max_body_len, len(action.body or ""))
        
    quality_score = 0.0
    if max_body_len > 20:
        quality_score = min(1.0, max_body_len / 200)
        
    # 4. Final Weighted Calculation
    final_score = 0.6 * issue_score_avg + 0.2 * verdict_avg + 0.2 * quality_score
    return float(max(0.0, min(1.0, final_score)))

