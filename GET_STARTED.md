# 🚀 Getting Started with CodeLens.

Welcome to **CodeLens.**, a production-grade AI agent evaluation environment. This guide will help you get up and running in less than 2 minutes.

---

## 1. Setup your Environment
First, create a virtual environment and install the required Python dependencies.

```bash
# Create and activate virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Initialize the Database
CodeLens uses SQLite for persistence. You must initialize the database before running the server for the first time.

```bash
# Initialize the codelens.db with 30 baseline scenarios
python scripts/migrate.py init
```

---

## 3. Launch the System
Start the FastAPI server. This serves both the **Agent API** and the **Interactive Dashboard**.

```bash
# Run the server
PYTHONPATH=. python app.py
```

---

## 4. Open the Dashboard
Once the server is running, you can access the CodeLens Dashboard at:

👉 **[http://localhost:7860/dashboard](http://localhost:7860/dashboard)**

From here, you can see the top-10 leaderboard and monitor live agent evaluations.

---

## 5. Run your First Evaluation
While keeping the server running in one terminal, open a **new terminal** and run the built-in Keyword agent to see results populated on the dashboard.

```bash
# Activate venv in the new terminal first!
source venv/bin/activate

# Run evaluation
python scripts/evaluate.py --agent keyword
```

---

## 🧪 Running Tests
To verify everything is working perfectly, you can run the full 155-test suite:

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## \ud83d\udee0 Troubleshooting Common Errors

### 1. `ModuleNotFoundError: No module named 'requests'`
This happens if you haven't activated the virtual environment in your current terminal tab.
- **Fix**: Run `source venv/bin/activate` in every new terminal window.

### 2. `Usage: python3 scripts/migrate.py [init|reset]`
The migration script requires an argument to proceed.
- **Fix**: Run `python scripts/migrate.py init` specifically.

### 3. Logo not appearing in Dashboard
If the logo shows a broken image placeholder:
- **Fix**: Re-run the server with `PYTHONPATH=. python app.py`. The backend now has optimized routing to serve the `logo.svg`.

---

> [!TIP]
> If you ever want to reset the database and start fresh with original scenarios, run:
> `python scripts/migrate.py reset`
