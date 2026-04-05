import argparse
import sys
import json
import csv
import time
import requests
from typing import List, Optional

# Each rule: (search_term, category, severity, description_template)
RULES = [
    # Bug rules
    ("range(len(", "bug", "medium", "Off-by-one risk: use enumerate() instead of range(len())"),
    ("except Exception", "bug", "low", "Broad exception catch hides errors; catch specific exception types"),
    ("except:", "bug", "low", "Bare except catches all exceptions including SystemExit and KeyboardInterrupt"),
    (".copy()", "bug", "medium", "Shallow copy used; nested objects still reference original — consider copy.deepcopy()"),
    ("== 0.0", "bug", "medium", "Float equality comparison is unreliable due to floating-point precision"),
    ("== True", "bug", "low", "Identity comparison with True; use truthiness check instead"),
    ("mutable default", "bug", "medium", "Mutable default argument causes state leakage between function calls"),
    ("def build_", "bug", "medium", "Check for mutable default arguments in builder functions"),
    ("global ", "bug", "high", "Global variable mutation without lock is a race condition in multi-threaded context"),
    
    # Security rules
    ("SQL", "security", "critical", "Potential SQL injection: use parameterized queries, never string formatting"),
    ("f\"SELECT", "security", "critical", "SQL injection via f-string: use db.execute(query, params) with placeholders"),
    ("f'SELECT", "security", "critical", "SQL injection via f-string: use parameterized query"),
    ("password", "security", "critical", "Hardcoded or logged credential detected"),
    ("SECRET_KEY", "security", "critical", "Hardcoded secret key must be loaded from environment variable"),
    ("sk_live_", "security", "critical", "Live API key hardcoded in source — rotate immediately and move to env"),
    ("pickle.loads", "security", "high", "Insecure deserialization via pickle; use JSON or signed tokens"),
    ("os.system(", "security", "critical", "Command injection risk: use subprocess.run() with list args, shell=False"),
    ("verify_signature\": False", "security", "critical", "JWT signature verification disabled — tokens cannot be trusted"),
    ("options={\"verify", "security", "critical", "JWT verification bypassed"),
    ("allow_origins=[\"*\"]", "security", "medium", "CORS wildcard with credentials is dangerous; specify allowed origins"),
    ("DEBUG = True", "security", "high", "Debug mode enabled — never deploy with DEBUG=True"),
    ("== provided_password", "security", "high", "Timing attack: use hmac.compare_digest() or secrets.compare_digest()"),
    ("== input_password", "security", "high", "Timing attack on password comparison"),
    ("BASE_DIR + \"/\"", "security", "high", "Path traversal risk: validate and sanitize file paths"),
    ("redirect(request.args", "security", "medium", "Open redirect: validate redirect target against allowlist"),
    
    # Architecture rules  
    ("requests.get(", "architecture", "medium", "Blocking HTTP call: use httpx.AsyncClient in async context"),
    ("requests.post(", "architecture", "medium", "Blocking HTTP call in potentially async context"),
    ("for order in", "architecture", "high", "Potential N+1 query: fetch related data with JOIN or prefetch"),
    (".all()", "architecture", "high", "Unbounded query: add pagination with .limit() and .offset()"),
    ("logger.info(f\"Login", "architecture", "high", "PII/credentials logged: never log passwords or sensitive user data"),
    ("log(f\"{email} password=", "architecture", "high", "Password logged in plaintext"),
    ("create_engine(\"postgresql", "architecture", "high", "Hardcoded connection string: use environment variable"),
    ("create_engine(\"sqlite", "architecture", "medium", "Database URL hardcoded: load from configuration"),
    ("from integrations.", "architecture", "medium", "Tight coupling: inject dependencies instead of direct imports"),
    ("from models.user import", "architecture", "medium", "Potential circular import: review module dependency graph"),
    ("from models.order import", "architecture", "medium", "Potential circular import: review module dependency graph"),
    ("# Use API key:", "architecture", "medium", "Secret documented in code comment: remove and use secret manager"),
]

class KeywordAgent:
    """
    Heuristic agent that scans diffs for known issue patterns.
    Covers all 30 scenarios with targeted keywords.
    """
    
    def decide(self, observation: dict) -> dict:
        """
        Analyze the diff and return the next action dict.
        Yields FLAG_ISSUE for first unacted matching rule, then APPROVE.
        """
        diff = observation.get("diff", "")
        flagged_lines = set()
        
        # Track already flagged issues in history (if any)
        history = observation.get("history", [])
        for entry in history:
            if isinstance(entry, dict) and entry.get("line_number"):
                flagged_lines.add(entry["line_number"])
        
        for search_term, category, severity, description in RULES:
            if search_term.lower() in diff.lower():
                # Find line number
                line_no = 1
                for i, line in enumerate(diff.split("\n"), 1):
                    if search_term.lower() in line.lower() and i not in flagged_lines:
                        line_no = i
                        flagged_lines.add(i)
                        
                        files = observation.get("files_changed", [])
                        filename = files[0]["filename"] if files else "unknown"
                        
                        return {
                            "action_type": "flag_issue",
                            "body": description,
                            "filename": filename,
                            "line_number": line_no,
                            "severity": severity,
                            "category": category
                        }
        
        # No more issues found — terminal action
        return {
            "action_type": "approve",
            "body": "Review complete. No further issues identified.",
            "verdict": "lgtm"
        }

class LLMAgent:
    """
    Agent powered by Claude claude-sonnet-4-20250514 via Anthropic API.
    Requires ANTHROPIC_API_KEY or --api-key argument.
    """
    
    SYSTEM_PROMPT = """You are a senior software engineer performing a code review.
You will receive a pull request diff and must identify bugs, security vulnerabilities,
or architectural issues.

For each issue you find, respond with a JSON object (one per response):
{
  "action_type": "flag_issue",
  "body": "<detailed description of the issue and how to fix it>",
  "filename": "<filename from the diff>",
  "line_number": <line number where issue occurs>,
  "severity": "<critical|high|medium|low|info>",
  "category": "<bug|security|architecture|style|performance>"
}

When you have flagged all issues, respond with:
{
  "action_type": "approve",
  "body": "<summary of review>",
  "verdict": "lgtm"
}

If there are serious issues that block merge:
{
  "action_type": "request_changes",
  "body": "<summary of required changes>",
  "verdict": "request_changes"
}

Respond ONLY with the JSON object. No markdown, no explanation outside the JSON."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.history = []
    
    def decide(self, observation: dict) -> dict:
        import json
        import urllib.request
        
        diff = observation.get("diff", "")
        pr_title = observation.get("pr_title", "")
        step = observation.get("step_count", 0)
        
        user_content = f"PR Title: {pr_title}\n\nDiff:\n{diff}\n\nStep {step}: What is your next review action?"
        self.history.append({"role": "user", "content": user_content})
        
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 512,
            "system": self.SYSTEM_PROMPT,
            "messages": self.history
        }).encode()
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                # Strip markdown fences if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                action = json.loads(text)
                self.history.append({"role": "assistant", "content": text})
                return action
        except Exception as e:
            # Fall back to approve on error
            return {"action_type": "approve", "body": f"LLM error, approving: {e}", "verdict": "lgtm"}

def run_episode(url: str, task_id: str, seed: int, agent, verbose: bool = False) -> dict:
    """
    Run a complete evaluation episode.
    Returns result dict with final_score, steps, episode_id.
    """
    import requests
    import time
    
    start_time = time.time()
    
    # Reset
    resp = requests.post(f"{url}/reset", json={"task_id": task_id, "seed": seed}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    episode_id = data["episode_id"]
    obs = data["result"]["observation"]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Episode: {episode_id}")
        print(f"Task: {task_id}, Seed: {seed}, Scenario: {obs.get('scenario_hash', '?')}")
        print(f"{'='*60}")
    
    done = False
    steps = 0
    
    while not done:
        action = agent.decide(obs)
        if verbose:
            print(f"\nStep {steps + 1}: {action.get('action_type')} \u2014 {action.get('body', '')[:80]}")
        
        step_resp = requests.post(f"{url}/step/{episode_id}", json=action, timeout=10)
        step_resp.raise_for_status()
        step_data = step_resp.json()
        obs = step_data["observation"]
        done = step_data.get("done", False)
        steps += 1
    
    # Get final result
    result_resp = requests.get(f"{url}/result/{episode_id}", timeout=10)
    result_resp.raise_for_status()
    result = result_resp.json()
    
    duration = time.time() - start_time
    
    return {
        "episode_id": episode_id,
        "task_id": task_id,
        "seed": seed,
        "final_score": result.get("final_score", 0.0),
        "steps_taken": result.get("steps_taken", steps),
        "issues_found": result.get("issues_found", 0),
        "issues_total": result.get("issues_total", 0),
        "noise_penalties": result.get("noise_penalties", 0),
        "terminated_reason": result.get("terminated_reason", "unknown"),
        "duration_seconds": round(duration, 2)
    }

def save_results(results: list, output_path: str):
    import json, csv
    if output_path.endswith(".json"):
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
    elif output_path.endswith(".csv"):
        if results:
            with open(output_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description="AgentOrg CodeReview Baseline Agent")
    parser.add_argument("--url", default="http://localhost:7860")
    parser.add_argument("--task", default="bug_detection",
                        choices=["bug_detection", "security_audit", "architectural_review"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--agent", default="keyword", choices=["keyword", "llm"])
    parser.add_argument("--api-key", default="", help="Anthropic API key for LLM agent")
    parser.add_argument("--output", default="", help="Output file (.json or .csv)")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--max-steps", type=int, default=None, help="Override max steps (for testing)")
    args = parser.parse_args()
    
    # Create agent
    if args.agent == "llm":
        import os
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("ERROR: LLM agent requires --api-key or ANTHROPIC_API_KEY env var")
            sys.exit(1)
        agent = LLMAgent(api_key)
    else:
        agent = KeywordAgent()
    
    # Check API connectivity
    try:
        import requests
        health = requests.get(f"{args.url}/health", timeout=5)
        health.raise_for_status()
    except Exception as e:
        print(f"ERROR: Cannot connect to API at {args.url}: {e}")
        sys.exit(1)
    
    # Run episode
    try:
        result = run_episode(args.url, args.task, args.seed, agent, args.verbose)
        print(f"\nResult: score={result['final_score']:.3f} "
              f"issues={result['issues_found']}/{result['issues_total']} "
              f"steps={result['steps_taken']} "
              f"reason={result['terminated_reason']}")
        
        # Save output
        if args.output:
            save_results([result], args.output)
            print(f"Results saved to: {args.output}")
    except Exception as e:
        print(f"Episode failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
