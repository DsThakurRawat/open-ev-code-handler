from typing import List, Optional
from codelens_env.models import GroundTruthIssue, Action

def keyword_overlap(body: str, keywords: List[str]) -> float:
    """Returns 0.0–1.0 confidence score based on keyword coverage."""
    if not body or not keywords:
        return 0.5  # Neutral credit for missing body or keywords
    
    body_lower = body.lower()
    hits = sum(1 for kw in keywords if kw.lower() in body_lower)
    
    # Roadmap logic: min(1.0, hits / max(4, len(keywords) * 0.6))
    threshold = max(4, len(keywords) * 0.6)
    return min(1.0, hits / threshold)

def find_best_match(action: Action, ground_truth: List[GroundTruthIssue], already_matched: set) -> Optional[GroundTruthIssue]:
    """Line-number match (exact-ish) OR category+file match."""
    for gt in ground_truth:
        if gt.id in already_matched:
            continue
        
        # Line number match within 3 lines
        line_match = (action.line_number is not None and 
                      abs(action.line_number - gt.line_number) <= 3)
        
        # Category and filename match
        cat_match = (action.category == gt.category and 
                     action.filename == gt.filename)
        
        if line_match or cat_match:
            return gt
            
    return None
