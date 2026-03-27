from typing import List
from codereview_env.models import Scenario, ActionRecord, Category
from codereview_env.graders.grader_utils import find_best_match

def grade_bug_detection(scenario: Scenario, history: List[ActionRecord]) -> float:
    """Grade bug detection: 0.4 * coverage + 0.6 * precision."""
    flagged_actions = [r for r in history if r.category == Category.BUG]
    if not scenario.ground_truth_issues:
        return 1.0 if not flagged_actions else 0.0
        
    found_ids = set()
    matches = 0
    already_matched = set()
    
    for action in flagged_actions:
        match = find_best_match(action, scenario.ground_truth_issues, already_matched)
        if match:
            matches += 1
            found_ids.add(match.id)
            already_matched.add(match.id)
            
    recall = len(found_ids) / len(scenario.ground_truth_issues)
    precision = matches / len(flagged_actions) if flagged_actions else 0.0
    
    return round(0.7 * recall + 0.3 * precision, 4)
