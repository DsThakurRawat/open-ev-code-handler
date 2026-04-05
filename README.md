<p align="center">
  <img src="assets/logo.svg" width="400" alt="CodeLens." />
</p>

# CodeLens

> **Can an AI agent catch the SQL injection that caused the $100M breach — before it ships?**

This environment trains and evaluates agents on realistic Python code reviews grounded in real-world incident patterns. Unlike toy examples, every scenario is calibrated against actual production failure modes: payment mutations without idempotency keys, JWT verification bypassed for "dev convenience," pickle deserialization opening RCE vectors.

[![CodeLens](https://img.shields.io/badge/CodeLens-1.0-blue)](https://huggingface.co/) [![Python 3.11](https://img.shields.io/badge/python-3.11-green)](https://python.org) [![FastAPI](https://img.shields.io/badge/FastAPI-0.109-red)](https://fastapi.tiangolo.com)

---

## Tasks

| Task | Difficulty | Max Steps | Scenarios | Focus |
|------|-----------|-----------|-----------|-------|
| `bug_detection` | Easy | 10 | 10 | Off-by-one, race conditions, None deref, type mismatches |
| `security_audit` | Medium | 15 | 10 | SQL injection, XSS, JWT bypass, pickle RCE, timing attacks |
| `architectural_review` | Hard | 20 | 10 | N+1 queries, god objects, missing idempotency, SRP violations |

---

## Observation Space

Each step the agent receives an `Observation` object:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `enum` | `bug_detection`, `security_audit`, or `architectural_review` |
| `pr_title` | `str` | Pull request title (incident-inspired framing) |
| `pr_description` | `str` | PR description from the author |
| `diff` | `str` | Unified diff of the PR |
| `files_changed` | `list[FileChange]` | Structured list of changed files |
| `step_count` | `int` | Current step (0-indexed start after reset) |
| `max_steps` | `int` | Maximum allowed steps for this task |
| `history` | `list[ActionRecord]` | All actions taken so far this episode |
| `noise_budget` | `int` | Remaining false-positive allowance (starts at 5) |
| `service_name` | `str` | Name of the service being reviewed |
| `service_criticality` | `"low"\|"medium"\|"high"\|"critical"` | How critical this service is to infrastructure |
| `blast_radius` | `"low"\|"medium"\|"high"\|"critical"` | How many users/systems a bug here would affect |
| `affected_users` | `int` | Estimated number of users impacted by a failure |

---

## Action Space

The agent submits one action per step as a typed `Action` object:

| `action_type` | Required Fields | Description |
|--------------|----------------|-------------|
| `flag_issue` | `body`, `filename`, `line_number`, `severity`, `category` | Flag a specific issue in the diff |
| `approve` | `body`, `verdict="LGTM"` | Approve the PR — no issues or all caught |
| `request_changes` | `body`, `verdict="REQUEST_CHANGES"` | Block merge — issues must be fixed |
| `comment` | `body` | Leave a general comment (no reward signal) |
| `ask_question` | `body` | Ask a clarifying question (no reward signal) |

**Valid severities:** `low`, `medium`, `high`, `critical`  
**Valid categories:** `bug`, `security`, `architecture`, `performance`, `style`, `design`

---

## Reward Function

Rewards are **incremental per step** (not end-of-episode):

| Event | Reward Delta |
|-------|-------------|
| Correctly flag a ground-truth issue | `+0.1` to `+0.7` (depends on full grader recalculation) |
| False positive flag | `-0.05` (consumes noise budget) |
| Correct terminal verdict (approve/request_changes) | Final grader score delta |
| Noise budget exhausted (5 FPs) | Episode terminates |

**Grader formulas:**
- **Bug:** `0.7 × recall + 0.3 × precision`
- **Security:** `0.7 × severity_accuracy + 0.3 × keyword_overlap` (normalized by GT issues)
- **Architecture:** `0.6 × issue_score + 0.2 × verdict_score + min(0.2, quality_bonus)`

---

## API Endpoints

```
POST /reset                    → ResetResponse (episode_id + initial observation)
POST /step/{episode_id}        → StepResult   (observation, reward, done, info)
GET  /state/{episode_id}       → StateResult  (step, score, issues_found, done)
GET  /result/{episode_id}      → EpisodeResult (final_score, issues_found/missed)
GET  /health                   → {"status": "ok", ...}
GET  /leaderboard              → top-10 per task
POST /submit                   → submit agent score to leaderboard
WS   /ws/events                → real-time step event stream
```

---

## Project Structure

```
.
├── inference.py              # Root inference script (CodeLens spec required)
├── app.py                    # FastAPI entry point
├── codelens.yaml              # CodeLens spec manifest
├── Dockerfile                # HuggingFace Spaces deployment
├── requirements.txt
├── codelens_env/
│   ├── env.py                # Episode state machine with incremental rewards
│   ├── models.py             # Pydantic models (Observation, Action, StateResult...)
│   ├── scenario_bank.py      # 30 scenarios with service metadata
│   └── graders/
│       ├── bug_grader.py     # Recall × Precision scoring
│       ├── security_grader.py # Severity accuracy + keyword overlap
│       ├── arch_grader.py    # Issue + verdict + quality scoring
│       └── grader_utils.py   # Line-number match + keyword overlap
└── tests/
    ├── test_env.py           # State machine + get_state() + reward tests
    └── test_graders.py       # Grader unit tests
```

---

## \ud83d\ude80 Quick Start

### 1. Setup Environment
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
# This creates the codelens.db with all standard scenarios
python scripts/migrate.py init
```

### 3. Launch CodeLens
```bash
PYTHONPATH=. python app.py
# API and Dashboard are now live at http://localhost:7860/dashboard
```

### 4. Run Evaluation (Baseline)
In a new terminal:
```bash
python scripts/evaluate.py --agent keyword
```

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="your-openai-key"
export ENV_URL="http://localhost:7860"

PYTHONPATH=. python inference.py
```

Output format:
```
[START] task=bug_detection env=http://localhost:7860 model=gpt-4o
[STEP] step=1 action='flag_issue' reward=0.7000 done=False error=None
[STEP] step=2 action='approve' reward=0.0000 done=True error=None
[END] success=True steps=2 score=0.7000 rewards=[0.7, 0.0]
```

---

## Baseline Scores

*Run `python inference.py` after starting the server to reproduce.*

| Task | Model | Avg Score | Success Rate |
|------|-------|-----------|-------------|
| `bug_detection` | gpt-3.5-turbo | ~0.52 | ~60% |
| `security_audit` | gpt-3.5-turbo | ~0.38 | ~40% |
| `architectural_review` | gpt-3.5-turbo | ~0.28 | ~30% |
| `bug_detection` | gpt-4o | ~0.74 | ~80% |
| `security_audit` | gpt-4o | ~0.61 | ~70% |
| `architectural_review` | gpt-4o | ~0.45 | ~50% |

> `architectural_review` is intentionally hard — frontier models score below 0.5 on average due to the need to reason about blast radius, idempotency, and service encapsulation simultaneously.

---

## Docker / HuggingFace Spaces

```bash
docker build -t codelens-env .
docker run -p 7860:7860 \
  -e PYTHONPATH=/app \
  codelens-env
```

The server starts automatically via `python app.py`.

---

## Features

- **30 Realistic Scenarios** — Incident-inspired PR titles tied to real service names, affected user counts, and blast radius labels
- **Deterministic Grading** — MoE-style confidence-weighted matching with explainable per-issue scoring rubrics  
- **Incremental Rewards** — Step-level reward signals (`+δ` per correct flag, `-0.05` per FP) enable proper RL training
- **Noise Budget** — Penalizes false positives to prevent reward gaming; episode terminates at 5 FPs
- **Blast Radius Context** — `affected_users`, `service_criticality`, `blast_radius` in every observation
- **WebSocket Stream** — Real-time step event broadcasting on `/ws/events`
- **Leaderboard** — In-memory top-10 tracking per task
- **Full CodeLens Spec** — `/reset`, `/step`, `/state`, `/result` + `[START]`/`[STEP]`/`[END]` stdout format
