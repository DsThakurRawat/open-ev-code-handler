# Contributing to CodeLens

Welcome! We appreciate contributions of all kinds. Here's how to get started.

---

##  Development Setup

To get started with local development:

1.  **Clone and Install**:
    ```bash
    git clone https://github.com/ArshVermaGit/open-ev-code-handler.git
    cd open-ev-code-handler
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Initialize**:
    ```bash
    cp .env.example .env
    python scripts/migrate.py init
    ```

3.  **Run Tests**:
    ```bash
    PYTHONPATH=. pytest tests/ -v
    ```

---

##  Adding a New Scenario

Scenarios live in `codelens_env/scenarios.py`. Each scenario needs:

**Step 1**: Choose a task type and next sequential hash (e.g., `bug_011`).

**Step 2**: Write a realistic unified diff. The diff must:
- Start with `--- a/filename` and `+++ b/filename`
- Include `@@ -N,M +N,M @@` hunk headers
- Show a few lines of context (unchanged lines)
- Include the problematic line prefixed with `+`

Example patch:
```python
patch="""--- a/api/users.py
+++ b/api/users.py
@@ -10,6 +10,6 @@ def get_users(page, size):
     offset = page * size
-    return items[offset:offset + size]
+    return items[offset:offset + size - 1]
"""
```

**Step 3**: Define at least one `GroundTruthIssue` with:
- `keywords`: 2+ specific terms an agent body must contain (case-insensitive)
- `line_number`: the line in the diff where the issue occurs (±3 tolerance for bugs/security, ±5 for arch)
- `severity`: appropriate level (`critical` only for RCE/auth bypass/data loss)

**Step 4**: Add to `ALL_SCENARIOS` list and verify:
```bash
PYTHONPATH=. python -m pytest tests/test_scenarios.py -v
```
All 30 (or more) scenarios must pass validation.

---

##  Pull Request Process

1. Fork the repo and create a branch: `feat/my-feature`, `fix/my-bug`, `test/more-tests`
2. Make your changes
3. Run the full test suite: `PYTHONPATH=. python -m pytest tests/ -v`
4. Run the linter: `pylint codelens_env/ app.py` (target score ≥ 7.0)
5. Open a PR against `main` with a clear description

---

##  Code Style

- **Type hints** on all public functions and methods
- **Docstrings** on all public classes and non-trivial functions
- **pylint score** ≥ 7.0
- **Line length** ≤ 100 characters
- No bare `except:` clauses — always specify the exception type

---

##  Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add rate limiting to /reset endpoint
fix: correct leaderboard rank calculation after slice
test: add parametrized tests for all 30 scenarios
docs: update README quick start commands
refactor: extract episode cleanup into separate module
chore: upgrade pydantic to 2.6.1
```
