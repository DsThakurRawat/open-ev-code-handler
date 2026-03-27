# AgentOrg CodeReview Environment

AI Senior Code Reviewer evaluation environment.

## Tasks
1. **Bug Detection**: Identify logical errors and edge cases.
2. **Security Audit**: Detect vulnerabilities (OWASP Top 10).
3. **Architectural Review**: Evaluate design patterns and system constraints.

## Project Structure

- `codereview_env/`: Core logic and state machine.
- `codereview_env/graders/`: Specialized grading modules (Bug, Security, Arch).
- `scripts/`: Operational scripts (baseline evaluation, validation).
- `tests/`: Comprehensive test suite.
- `app.py`: FastAPI entry point.
- `openenv.yaml`: OpenEnv specification.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Environment

### 1. Start the API Server
```bash
PYTHONPATH=. python3 app.py
```
*Server runs on port **7860** (Hugging Face standard).*

### 2. Run Baseline Agent
```bash
PYTHONPATH=. python3 scripts/baseline.py --url http://localhost:7860
```

## Features
- **Deterministic Grading**: MoE-inspired confidence-weighted matching.
- **Noise Budget**: Penalizes false positives to prevent gaming the system.
- **WebSocket Stream**: Real-time event broadcasting on `/ws/events`.
- **Leaderboard**: In-memory tracking of top agent performances.

## Verification

Run the full test suite to ensure everything is functional:

```bash
PYTHONPATH=. pytest tests/
```

Individual component tests:
- `tests/test_graders.py`: Scoring logic unit tests.
- `tests/test_env.py`: State machine integration tests.
- `tests/test_api.py`: FastAPI contract tests.

## Roadmap & Progress
The environment is currently **Production Ready** and follows the standard OpenEnv specification.
- [x] 30 Synthetic Scenarios (Bug, Security, Architecture)
- [x] Deterministic specialized graders
- [x] Thin FastAPI gateway with WebSocket event streaming
- [x] Comprehensive test coverage
