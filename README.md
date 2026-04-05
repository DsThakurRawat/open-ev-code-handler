<p align="center">
  <img src="assets/codelens-brand-v2.svg" width="400" alt="CodeLens." />
</p>

# CodeLens Environment

![CI](https://github.com/ArshVermaGit/open-ev-code-handler/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)

> **AI evaluation environment for benchmarking code review agents on 30 synthetic pull requests.**

CodeLens is a high-fidelity evaluation environment where AI agents act as senior code reviewers. They analyze pull request diffs to identify bugs, security vulnerabilities, and architectural issues before providing a final verdict.

Designed for researchers and developers building the next generation of AI code assistants, CodeLens provides 30 realistic Python scenarios with ground-truth labels and deterministic, reproducible scoring.

---

## 🚀 Quick Start

Get up and running locally in under 2 minutes:

```bash
git clone https://github.com/ArshVermaGit/open-ev-code-handler.git
cd open-ev-code-handler
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/migrate.py init
PYTHONPATH=. python app.py
```

- **Dashboard**: [http://localhost:7860/dashboard](http://localhost:7860/dashboard)
- **API Docs**: [http://localhost:7860/docs](http://localhost:7860/docs)

---

## 📋 Evaluation Tasks

CodeLens benchmarks agents across three critical engineering domains:

| Task | Scenarios | Max Steps | Focus Area |
|------|-----------|-----------|------------|
| `bug_detection` | 10 | 10 | Off-by-one errors, null dereferences, race conditions, exception handling |
| `security_audit` | 10 | 15 | SQL injection, hardcoded secrets, path traversal, insecure deserialization |
| `architectural_review` | 10 | 20 | N+1 queries, god classes, blocking async calls, circular imports |

---

## 📈 Scoring System

### Bug Detection
Score = `0.4 × coverage + 0.6 × avg_issue_score − 0.1 × false_positive_rate`
Issues are scored on **keyword accuracy** (50%) and **severity matching** (50%).

### Security Audit
Score = `avg(per_issue_score)` where each issue = `0.7 × severity_accuracy + 0.3 × keyword_coverage`.
Severity accuracy is distance-weighted: misclassifying a **CRITICAL** issue as **LOW** incurs a major penalty.

### Architectural Review
Score = `0.6 × detection_rate + 0.2 × verdict_accuracy + 0.2 × detail_quality`.
Detail quality rewards technical explanations that provide actionable developer feedback.

### 🛑 Noise Budget
Every episode permits **5 false positive credits**. Flagging non-existent code paths spends one credit. Reaching zero terminates the episode immediately to prevent agent hallucination loops.

---

## 🔌 API Reference

| Method | Endpoint | Auth | Description |
|:-------|:---------|:-----|:------------|
| `POST` | `/reset` | Optional | Start a new evaluation episode |
| `POST` | `/step/{id}` | Optional | Submit a review action (flag_issue, approve) |
| `GET` | `/result/{id}` | Optional | Retrieve final scores and logs for an episode |
| `GET` | `/leaderboard` | None | Paginated performance rankings |
| `POST` | `/submit` | Optional | Persist an episode result to the leaderboard |
| `GET` | `/stats` | None | Aggregate statistics across all agents |
| `GET` | `/episodes/{id}/replay` | Optional | Full event-by-event history replay |
| `GET` | `/dashboard` | None | Interactive Real-time Dashboard |
| `GET` | `/health` | None | System status and health check |

Authentication is disabled by default. Set `API_KEY_ENABLED=true` in `.env` for production parity.

---

## 🐳 Running with Docker

### Production Mode
```bash
docker compose up -d
# View logs: docker compose logs -f
```

### Direct Pull
```bash
docker run -p 7860:7860 ghcr.io/ArshVermaGit/open-ev-code-handler:latest
```

### Automated Testing
```bash
docker compose -f docker-compose.test.yml up
```

---

## 🤖 Baseline Agent & Evaluation

### Single Scenario Trial
```bash
python scripts/baseline.py --task bug_detection --seed 3 --verbose
```

### Full Benchmark (All 30 Scenarios)
```bash
# Keyword-based baseline
python scripts/evaluate.py --agent keyword --output results.json

# LLM-powered reviewer (e.g. Claude)
python scripts/evaluate.py --agent llm --api-key $ANTHROPIC_API_KEY
```

---

## 🧠 Writing Your Own Agent

CodeLens is designed to be agent-agnostic. Use standard HTTP requests to build your reviewer:

```python
import requests

API = "http://localhost:7860"

# Start new episode
resp = requests.post(f"{API}/reset", json={"task_id": "bug_detection", "seed": 0})
episode_id = resp.json()["episode_id"]

done = False
while not done:
    # Your agent logic analyzes the diff
    action = {
        "action_type": "flag_issue",
        "body": "Identified a vulnerability line 14",
        "filename": "api/search.py",
        "line_number": 14,
        "severity": "critical",
        "category": "security"
    }
    
    result = requests.post(f"{API}/step/{episode_id}", json=action).json()
    done = result["done"]

# Get final results
final = requests.get(f"{API}/result/{episode_id}").json()
print(f"Final Score: {final['final_score']}")
```

---

## 📂 Project Structure

```text
open-ev-code-handler/
├── app.py                      # FastAPI application (9 endpoints)
├── codelens_env/               # Core evaluation logic
│   ├── database.py             # SQLModel persistence layer
│   ├── env.py                  # Episode state machine
│   ├── models.py               # Pydantic v2 data models
│   ├── scenarios.py            # 30 Synthetic PR scenarios
│   └── graders/                # Grader implementations (Bug, Sec, Arch)
├── scripts/                    # CLI tools (baseline, evaluate, migrate)
├── static/                     # Compiled dashboard assets
├── tests/                      # 155+ Parametrized tests
├── Dockerfile                  # Multi-stage, non-root build
├── docker-compose.yml          # Production orchestration
└── codelens.yaml               # CodeLens v2 specification
```

---

## 🛠️ Development

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Automated Tests
PYTHONPATH=. pytest tests/ -v --cov=codelens_env

# Linter Check
pylint codelens_env/ app.py

# Scenario Sanity Check
PYTHONPATH=. python scripts/validate.py
```

---

## 📄 Contributing & License
Please see **[CONTRIBUTING.md](CONTRIBUTING.md)** for details on authoring new scenarios and submission standards.

This project is licensed under the **[MIT License](LICENSE)**.
