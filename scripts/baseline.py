import requests
from codereview_env.models import TaskId, ActionType, Category, Severity, Verdict

API_URL = "http://localhost:7860"

def run_baseline(task_id: TaskId, seed: int = 42):
    # 1. Reset
    resp = requests.post(f"{API_URL}/reset", json={"task_id": task_id, "seed": seed})
    resp.raise_for_status()
    data = resp.json()
    episode_id = data["episode_id"]
    obs = data["result"]["observation"]
    
    print(f"Started episode {episode_id} for task {task_id}")
    
    # 2. Simple keyword-based logic
    # Look for common bug/security keywords in the diff
    keywords = {
        "SQL": (Category.SECURITY, Severity.CRITICAL, "Potential SQL injection detected."),
        "password": (Category.SECURITY, Severity.HIGH, "Hardcoded credential detected."),
        "range(len": (Category.BUG, Severity.MEDIUM, "Off-by-one error suspected."),
        "Exception": (Category.BUG, Severity.LOW, "Broad exception catch detected.")
    }
    
    # Simple loop
    done = False
    while not done:
        diff = obs["diff"]
        action = None
        
        for kw, (cat, sev, desc) in keywords.items():
            if kw in diff:
                # Find line number (very naive)
                line_no = 1
                for i, line in enumerate(diff.split("\n")):
                    if kw in line:
                        line_no = i + 1
                        break
                        
                action = {
                    "action_type": ActionType.FLAG_ISSUE,
                    "body": desc,
                    "filename": obs["files_changed"][0]["filename"] if obs["files_changed"] else "unknown",
                    "line_number": line_no,
                    "severity": sev,
                    "category": cat
                }
                break
        
        if not action:
            # Terminal action
            action = {
                "action_type": ActionType.APPROVE if task_id != TaskId.ARCHITECTURAL_REVIEW else ActionType.REQUEST_CHANGES,
                "verdict": Verdict.LGTM if task_id != TaskId.ARCHITECTURAL_REVIEW else Verdict.REQUEST_CHANGES,
                "body": "LGTM" if task_id != TaskId.ARCHITECTURAL_REVIEW else "Architectural issues found."
            }
            
        step_resp = requests.post(f"{API_URL}/step/{episode_id}", json=action)
        step_resp.raise_for_status()
        step_data = step_resp.json()
        obs = step_data["observation"]
        done = step_data["done"]
        
    # 3. Get final result
    result_resp = requests.get(f"{API_URL}/result/{episode_id}")
    result_resp.raise_for_status()
    print(f"Final Score: {result_resp.json()['final_score']}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the baseline agent against the CodeReview API.")
    parser.add_argument("--url", default="http://localhost:7860", help="Base URL of the running API (default: http://localhost:7860)")
    parser.add_argument("--task", default="bug_detection", help="Task ID to run (default: bug_detection)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (default: 0)")
    args = parser.parse_args()

    # Override module-level API_URL with CLI argument
    API_URL = args.url

    # Map string task id to TaskId enum
    task_map = {t.value: t for t in TaskId}
    if args.task not in task_map:
        parser.error(f"Unknown task '{args.task}'. Choose from: {list(task_map.keys())}")

    try:
        run_baseline(task_map[args.task], seed=args.seed)
    except Exception as e:
        print(f"Baseline failed (is the API running?): {e}")
