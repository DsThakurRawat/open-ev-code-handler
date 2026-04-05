#!/usr/bin/env python3
"""
Batch evaluation: runs all 30 scenarios and prints a summary report.
Usage: python scripts/evaluate.py --url http://localhost:7860 --agent keyword --output results.json
"""

import argparse
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.baseline import KeywordAgent, LLMAgent, run_episode, save_results

TASKS = ["bug_detection", "security_audit", "architectural_review"]
SEEDS = list(range(10))

def run_batch_evaluation(url: str, agent, verbose: bool = False) -> list:
    """Run all 30 scenarios and return results."""
    all_results = []
    
    for task in TASKS:
        print(f"\n\u2500\u2500 Task: {task} \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
        for seed in SEEDS:
            try:
                result = run_episode(url, task, seed, agent, verbose)
                all_results.append(result)
                score = result["final_score"]
                bar = "\u2588" * int(score * 10) + "\u2591" * (10 - int(score * 10))
                print(f"  Seed {seed:2d}: [{bar}] {score:.3f}  ({result['issues_found']}/{result['issues_total']} issues)")
            except Exception as e:
                print(f"  Seed {seed:2d}: FAILED \u2014 {e}")
                all_results.append({"task_id": task, "seed": seed, "final_score": 0.0, "error": str(e)})
    
    return all_results

def print_summary(results: list):
    """Print a formatted summary report."""
    from collections import defaultdict
    import statistics
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    by_task = defaultdict(list)
    for r in results:
        if "error" not in r:
            by_task[r["task_id"]].append(r["final_score"])
    
    overall_scores = [s for scores in by_task.values() for s in scores]
    
    for task, scores in by_task.items():
        if scores:
            print(f"\n{task.upper().replace('_', ' ')}")
            print(f"  Mean:   {statistics.mean(scores):.3f}")
            print(f"  Median: {statistics.median(scores):.3f}")
            print(f"  Stdev:  {statistics.stdev(scores) if len(scores) > 1 else 0:.3f}")
            print(f"  Best:   {max(scores):.3f}")
            print(f"  Worst:  {min(scores):.3f}")
    
    if overall_scores:
        print(f"\nOVERALL ({len(overall_scores)}/30 scenarios)")
        print(f"  Mean score: {statistics.mean(overall_scores):.3f}")
        print(f"  Success rate (>0.5): {sum(1 for s in overall_scores if s > 0.5)/len(overall_scores)*100:.1f}%")
    
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Batch evaluation of all 30 CodeLens scenarios")
    parser.add_argument("--url", default="http://localhost:7860")
    parser.add_argument("--agent", default="keyword", choices=["keyword", "llm"])
    parser.add_argument("--api-key", default="")
    parser.add_argument("--output", default="results.json", help="Output file (.json or .csv)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--task", default=None,
                        choices=["bug_detection", "security_audit", "architectural_review", None],
                        help="Run only a specific task (default: all)")
    args = parser.parse_args()
    
    if args.agent == "llm":
        import os
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("ERROR: LLM agent requires --api-key or ANTHROPIC_API_KEY env var")
            sys.exit(1)
        agent = LLMAgent(api_key)
    else:
        agent = KeywordAgent()
    
    # Check connectivity
    try:
        import requests
        requests.get(f"{args.url}/health", timeout=5).raise_for_status()
    except Exception as e:
        print(f"ERROR: Cannot connect to {args.url}: {e}")
        sys.exit(1)
    
    global TASKS
    if args.task:
        TASKS = [args.task]
    
    print(f"Running evaluation: {len(TASKS)} task(s), {len(SEEDS)} seeds each")
    print(f"Agent: {args.agent} | API: {args.url}")
    start = time.time()
    
    results = run_batch_evaluation(args.url, agent, args.verbose)
    
    print(f"\nCompleted in {time.time()-start:.1f}s")
    print_summary(results)
    
    if args.output:
        save_results(results, args.output)
        print(f"\nResults saved to: {args.output}")

if __name__ == "__main__":
    main()
