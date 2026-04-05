# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-04-05

### Added
- **Models**: Complete Pydantic v2 models (`TaskId`, `Action`, `Scenario`, `EpisodeResult`, etc.)
- **Scenarios**: 30 synthetic PR scenarios (10 per task) with realistic Python diffs
- **Env**: Full episode state machine with noise budget, reward calculation, and history tracking
- **Graders**: 
  - `bug_grader.py`: Coverage + precision + severity-weighted scoring
  - `security_grader.py`: Severity-accuracy-weighted scoring (CRITICAL misclassification penalized)
  - `arch_grader.py`: Binary issue detection + verdict scoring + detail quality bonus
- **Config**: Pydantic-settings config with all options documented in `.env.example`
- **Database**: SQLModel persistence (`EpisodeRecord`, `LeaderboardRecord`, helpers)
- **API Endpoints**:
  - `GET /stats`: Aggregate metrics across all recorded episodes
  - `GET /episodes/{id}/replay`: Full action-by-action replay for completed episodes
  - `GET /episodes`: List active episodes with metadata
  - `GET /dashboard`: Web dashboard (dark theme, live leaderboard, WebSocket event feed, stats cards)
- **Security**:
  - Rate limiting via `slowapi`: 60 req/min per IP (configurable)
  - API key authentication: optional, off by default, enabled via `API_KEY_ENABLED=true`
- **Episode Lifecycle**: Auto-cleanup of expired episodes every 5 minutes (default 1hr)
- **Leaderboard**: Paginated `/leaderboard?limit=N&offset=M&task_id=X`
- **Baseline Agent**: Full rewrite with argparse CLI, `KeywordAgent` (35 rules), `LLMAgent` (Claude)
- **Evaluation**: `scripts/evaluate.py` for batch evaluation of all 30 scenarios with summary report and progress bars
- **Database Utility**: `scripts/migrate.py` for database init/reset commands
- **Testing**: 
  - `tests/conftest.py`: Shared fixtures with in-memory DB override
  - `tests/test_scenarios.py`: 30 parametrized scenario validation tests
  - `tests/test_database.py`: Persistence layer unit tests
- **Dockerization**: Multi-stage `builder` + `production` builds with non-root user security
- **CI/CD**: Unified 5-job pipeline (`lint`, `test`, `validate`, `docker-build`, `publish` to GHCR)
- **Branding**: Full rebrand to **CodeLens.**, including signature typography and SVG iconography

### Fixed
- **CLI**: Port mismatch in `baseline.py` (8000 → 7860) and added `--url`, `--task`, `--seed` CLI flags
- **Crash Fixes**: Leaderboard submit crash after list slicing (captured rank before slice)
- **WebSocket**: Disconnect now handled with typed `WebSocketDisconnect` and `clients.discard()`
- **Metadata**: Incoherent weight structure in `codelens.yaml` replaced with named, accurate pairs

### Changed
- **Response Format**: `/leaderboard` response format: each task now `{"entries": [...], "total": N}` (was bare list)
- **Startup**: `app.py` startup initializes DB and logs confirmation message

## [1.0.0] - Original Fork Baseline

### Added
- FastAPI skeleton with /reset, /step, /result, /leaderboard, /submit endpoints
- In-memory episode storage
- WebSocket event broadcasting at /ws/events
- Basic Dockerfile
- Pylint-only GitHub Actions workflow
- codelens.yaml placeholder
- README with roadmap
