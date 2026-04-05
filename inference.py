"""
CodeLens Inference Script — CodeLens Environment
==========================================================
Required env vars:
  API_BASE_URL  — OpenAI-compatible base URL  (e.g. https://api.openai.com/v1)
  MODEL_NAME    — Model identifier             (e.g. gpt-4o, gpt-3.5-turbo)
  HF_TOKEN      — Hugging Face token (used as api_key for OpenAI client)
  ENV_URL       — CodeLens env URL           (default: http://localhost:7860)

Output format (stdout, per CodeLens spec):
  [START] task=<task_id> env=<env_url> model=<model>
  [STEP] step=<n> action=<str> reward=<float> done=<bool> error=<str|None>
  [END] success=<bool> steps=<int> score=<float> rewards=<list>
"""

import os
import sys
import json
import time
import requests
from openai import OpenAI

# ── Environment Variables (exact names required by CodeLens spec) ──────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN     = os.environ.get("HF_TOKEN", "dummy")
ENV_URL      = os.environ.get("ENV_URL", "http://localhost:7860")

# ── Config ────────────────────────────────────────────────────────────────────
TASKS             = ["bug_detection", "security_audit", "architectural_review"]
MAX_STEPS         = {"bug_detection": 10, "security_audit": 15, "architectural_review": 20}
SUCCESS_THRESHOLD = 0.5
SEEDS             = [0, 1, 2]   # Run each task on 3 seeds for robust baseline

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)


# ── Structured log helpers (mandatory CodeLens format) ─────────────────────────
def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error):
    print(
        f"[STEP] step={step} action={action!r} reward={reward:.4f} "
        f"done={done} error={error}",
        flush=True
    )

def log_end(success: bool, steps: int, score: float, rewards: list):
    print(
        f"[END] success={success} steps={steps} score={score:.4f} "
        f"rewards={rewards}",
        flush=True
    )


# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert code reviewer specializing in bugs, security vulnerabilities, and architectural issues.

You will be given a code diff (PR) to review. Your job is to identify issues and output a single JSON action.

Available action types:
  - "flag_issue": Flag a specific issue in the code
  - "approve": Approve the PR (no issues found / all issues flagged)
  - "request_changes": Request changes (issues found that must be fixed)
  - "ask_question": Ask a clarifying question
  - "comment": Leave a general comment

For "flag_issue", you MUST provide:
  - action_type: "flag_issue"
  - body: description of the issue (be specific, mention the root cause)
  - filename: the file containing the issue
  - line_number: approximate line number
  - severity: one of "low", "medium", "high", "critical"
  - category: one of "bug", "security", "architecture", "performance", "style", "design"

For "approve" or "request_changes", you MUST provide:
  - action_type: "approve" or "request_changes"
  - body: your overall assessment
  - verdict: "LGTM" (for approve) or "REQUEST_CHANGES" (for request_changes)

After flagging all issues you can find, submit an approve or request_changes action.

IMPORTANT: Output ONLY a valid JSON object — no markdown, no explanation.
"""


def build_user_message(obs: dict, task_id: str, step: int) -> str:
    """Build the user message from the current observation."""
    task_hints = {
        "bug_detection": "Focus on: off-by-one errors, None dereferences, type mismatches, mutable defaults, race conditions, exception handling.",
        "security_audit": "Focus on: SQL injection, XSS, hardcoded secrets, JWT issues, insecure deserialization, CORS, timing attacks, path traversal.",
        "architectural_review": "Focus on: SRP violations, direct DB access from wrong layers, N+1 queries, missing retry/circuit-breaker, god objects, blocking I/O."
    }

    service_info = ""
    if obs.get("service_criticality") or obs.get("blast_radius"):
        service_info = f"""
Service Context:
  - Service Criticality: {obs.get('service_criticality', 'unknown')}
  - Blast Radius: {obs.get('blast_radius', 'unknown')}
  - Affected Users: {obs.get('affected_users', 'unknown')}
"""

    history_summary = ""
    if obs.get("history"):
        history_summary = f"\nPreviously flagged {len(obs['history'])} issue(s). Don't re-flag the same issue.\n"

    return f"""PR Title: {obs.get('pr_title', 'N/A')}
PR Description: {obs.get('pr_description', 'N/A')}
Task: {task_id} (step {step}/{obs.get('max_steps', '?')})
Noise budget remaining: {obs.get('noise_budget', '?')} (false positives consume this){service_info}
Review focus: {task_hints.get(task_id, 'General code review')}
{history_summary}
Code diff:
```
{obs.get('diff', '(no diff available)')}
```

Output a single JSON action object. If you've already flagged the main issues, submit approve or request_changes."""


def call_llm(messages: list) -> dict:
    """Call the LLM with retries and parse its JSON response."""
    last_err = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            
            # Robust JSON extract (some models might still use markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                 content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    
    raise last_err or Exception("LLM call failed after retries")


def sanitize_action(action_dict: dict, task_id: str) -> dict:
    """Ensure the action dict is valid and won't be rejected by the server."""
    action_type = action_dict.get("action_type", "comment")

    # Ensure category matches the task if flagging
    if action_type == "flag_issue":
        task_category_map = {
            "bug_detection": "bug",
            "security_audit": "security",
            "architectural_review": "architecture",
        }
        if "category" not in action_dict or action_dict["category"] not in [
            "bug", "security", "architecture", "performance", "style", "design"
        ]:
            action_dict["category"] = task_category_map.get(task_id, "bug")

        if "severity" not in action_dict or action_dict["severity"] not in [
            "low", "medium", "high", "critical"
        ]:
            action_dict["severity"] = "medium"

        if "filename" not in action_dict or not action_dict["filename"]:
            action_dict["filename"] = "unknown"

        if "line_number" not in action_dict:
            action_dict["line_number"] = 1

        if "body" not in action_dict or not action_dict["body"]:
            action_dict["body"] = "Issue detected"

    elif action_type in ("approve", "request_changes"):
        if action_type == "approve":
            action_dict["verdict"] = "lgtm"
        else:
            action_dict["verdict"] = "request_changes"
        if "body" not in action_dict:
            action_dict["body"] = "Review complete."

    return action_dict


def run_episode(task_id: str, seed: int) -> dict:
    """Run a single episode. Returns {score, steps, success, rewards}."""
    log_start(task_id, ENV_URL, MODEL_NAME)

    # ── Reset ──────────────────────────────────────────────────────────────
    try:
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            json={"task_id": task_id, "seed": seed},
            timeout=10
        )
        reset_resp.raise_for_status()
    except Exception as e:
        log_end(False, 0, 0.0, [])
        return {"score": 0.0, "steps": 0, "success": False, "rewards": [], "error": str(e)}

    reset_data = reset_resp.json()
    episode_id = reset_data["episode_id"]
    obs        = reset_data["result"]["observation"]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    rewards  = []
    step     = 0
    done     = False
    max_s    = MAX_STEPS.get(task_id, 15)

    # ── Step loop ──────────────────────────────────────────────────────────
    while not done and step < max_s:
        step += 1
        user_msg = build_user_message(obs, task_id, step)
        messages.append({"role": "user", "content": user_msg})

        error_msg = None
        try:
            action_dict = call_llm(messages)
            action_dict = sanitize_action(action_dict, task_id)

            step_resp = requests.post(
                f"{ENV_URL}/step/{episode_id}",
                json=action_dict,
                timeout=15
            )
            step_resp.raise_for_status()
            step_data = step_resp.json()

            reward = step_data.get("reward", 0.0)
            done   = step_data.get("done", False)
            obs    = step_data.get("observation", obs)

            rewards.append(round(reward, 4))

            # Add assistant turn to conversation
            messages.append({
                "role": "assistant",
                "content": json.dumps(action_dict)
            })

        except Exception as e:
            error_msg = str(e)
            reward = 0.0
            done = True  # Stop on unrecoverable error

        log_step(step, action_dict.get("action_type", "unknown") if error_msg is None else "error",
                 reward, done, error_msg)

        if error_msg:
            break

    # ── Get final result ───────────────────────────────────────────────────
    try:
        result_resp = requests.get(f"{ENV_URL}/result/{episode_id}", timeout=10)
        result_resp.raise_for_status()
        result_data = result_resp.json()
        final_score = result_data.get("final_score", 0.0)
    except Exception:
        final_score = rewards[-1] if rewards else 0.0

    success = final_score >= SUCCESS_THRESHOLD
    log_end(success, step, final_score, rewards)

    return {
        "task_id": task_id,
        "seed": seed,
        "score": final_score,
        "steps": step,
        "success": success,
        "rewards": rewards
    }


def main():
    """Run all tasks across multiple seeds and print a summary."""
    print("=" * 60, flush=True)
    print(f"CodeLens Baseline", flush=True)
    print(f"Model:  {MODEL_NAME}", flush=True)
    print(f"EnvURL: {ENV_URL}", flush=True)
    print("=" * 60, flush=True)

    all_results = []

    for task_id in TASKS:
        task_scores = []
        for seed in SEEDS:
            print(f"\n--- Task: {task_id} | Seed: {seed} ---", flush=True)
            result = run_episode(task_id, seed)
            all_results.append(result)
            task_scores.append(result["score"])

        avg_score = sum(task_scores) / len(task_scores) if task_scores else 0.0
        print(f"\n[SUMMARY] task={task_id} avg_score={avg_score:.4f} seeds={SEEDS}", flush=True)

    # ── Overall baseline table ─────────────────────────────────────────────
    print("\n" + "=" * 60, flush=True)
    print("BASELINE RESULTS", flush=True)
    print("=" * 60, flush=True)
    print(f"{'Task':<30} {'Avg Score':>10} {'Success Rate':>14}", flush=True)
    print("-" * 56, flush=True)

    for task_id in TASKS:
        task_results = [r for r in all_results if r["task_id"] == task_id]
        avg   = sum(r["score"] for r in task_results) / len(task_results)
        succ  = sum(1 for r in task_results if r["success"]) / len(task_results)
        print(f"{task_id:<30} {avg:>10.4f} {succ*100:>13.1f}%", flush=True)

    overall = sum(r["score"] for r in all_results) / len(all_results)
    print("-" * 56, flush=True)
    print(f"{'OVERALL':<30} {overall:>10.4f}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
