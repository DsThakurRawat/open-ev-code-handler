import sys
from codereview_env.models import TaskId
from codereview_env.env import CodeReviewEnv

def validate_environment():
    print("=== OpenEnv Validation Suite ===")
    env = CodeReviewEnv()
    
    tasks = [TaskId.BUG_DETECTION, TaskId.SECURITY_AUDIT, TaskId.ARCHITECTURAL_REVIEW]
    total_scenarios = 30
    passed = 0
    
    for task in tasks:
        print(f"\nValidating Task: {task}")
        for seed in range(10): # Check first 10 scenarios per task
            try:
                env.reset(task, seed=seed)
                passed += 1
                print(f"  [PASS] Scenario {seed}")
            except Exception as e:
                print(f"  [FAIL] Scenario {seed}: {e}")
                
    print(f"\nFinal Result: {passed}/{total_scenarios} scenarios reachable.")
    if passed == 30:
        print("ENVIRONMENT VALIDATED SUCCESSFULLY.")
        sys.exit(0)
    else:
        print("VALIDATION FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    validate_environment()
