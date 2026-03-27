import random
from codereview_env.models import (
    Scenario, FileChange, GroundTruthIssue, Category, Severity, TaskId, Verdict
)

def get_scenario(task_id: TaskId, seed: int) -> Scenario:
    rng = random.Random(seed)
    bank = SCENARIOS.get(task_id, [])
    if not bank:
        raise ValueError(f"No scenarios found for task: {task_id}")
    
    import hashlib
    import json
    idx = rng.randint(0, len(bank) - 1)
    scenario = bank[idx]
    # Dynamic hash as per roadmap
    scenario_dict = scenario.model_dump()
    content = json.dumps(scenario_dict, sort_keys=True).encode()
    scenario.hash = hashlib.md5(content).hexdigest()
    return scenario

# --- BUG DETECTION SCENARIOS (10) ---
BUG_SCENARIOS = [
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Fix: Off-by-one error in list processing",
        pr_description="Processing elements in the list but missing the last one due to range(len(x)-1).",
        files_changed=[
            FileChange(
                filename="utils.py",
                patch="""@@ -10,1 +10,1 @@
-    for i in range(len(items) - 1):
+    for i in range(len(items)):
+        print(items[i])""",
                additions=2,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_001",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="utils.py",
                line_number=10,
                description="Off-by-one error in list processing loop. Should use range(len(items)).",
                keywords=["off-by-one", "index", "out of range", "boundary", "loop"]
            )
        ],
        hash="bug_001_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Add: Mutable default argument to fetch_data",
        pr_description="New helper to fetch data with a default empty list for items.",
        files_changed=[
            FileChange(
                filename="api_client.py",
                patch="""@@ -5,1 +5,1 @@
-def fetch_data(url: str, headers: dict = None):
+def fetch_data(url: str, items: list = []):
+    items.append(url)
+    return items""",
                additions=2,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_002",
                category=Category.BUG,
                severity=Severity.HIGH,
                filename="api_client.py",
                line_number=5,
                description="Mutable default argument in Python. Items list will be shared across calls.",
                keywords=["mutable", "default", "argument", "persistent", "shared state"]
            )
        ],
        hash="bug_002_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="None dereference in user lookup",
        pr_description="Lookup user by ID and access properties without guard.",
        files_changed=[
            FileChange(
                filename="auth.py",
                patch="""@@ -15,1 +15,2 @@
 def get_user_role(uid):
-    user = db.users.get(uid)
+    user = db.users.get(uid)
+    return user.role""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_003",
                category=Category.BUG,
                severity=Severity.HIGH,
                filename="auth.py",
                line_number=16,
                description="Potential None dereference. user might be None if ID is not found.",
                keywords=["None", "null check", "KeyError", "AttributeError", "guard clause"]
            )
        ],
        hash="bug_003_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Assignment in conditional",
        pr_description="Check if setting is enabled and update status.",
        files_changed=[
            FileChange(
                filename="config_manager.py",
                patch="""@@ -8,1 +8,1 @@
-    if config.enabled == True:
+    if config.status = "active":
+        process_config(config)""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_004",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="config_manager.py",
                line_number=8,
                description="Assignment operator used in conditional statement. Should be '=='.",
                keywords=["assignment", "comparison", "conditional", "operator", "typo"]
            )
        ],
        hash="bug_004_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Integer overflow in loop counter",
        pr_description="Counter for processed records doesn't reset.",
        files_changed=[
            FileChange(
                filename="processor.py",
                patch="""@@ -25,1 +25,3 @@
-    processed_count = 0
+    processed_count += 1
+    if processed_count > 1000000:
+        log.warning("High volume")""",
                additions=2,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_005",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="processor.py",
                line_number=25,
                description="Integer overflow or lack of reset in counter. Can lead to boundary issues.",
                keywords=["overflow", "counter", "integer", "reset", "boundary", "infinite"]
            )
        ],
        hash="bug_005_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Race condition in cache update",
        pr_description="Parallel threads updating shared cache without locking.",
        files_changed=[
            FileChange(
                filename="cache_store.py",
                patch="""@@ -12,1 +12,2 @@
 def update_cache(key, val):
-    cache[key] = val
+    old_val = cache[key]
+    cache[key] = old_val + val""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_006",
                category=Category.BUG,
                severity=Severity.HIGH,
                filename="cache_store.py",
                line_number=13,
                description="Race condition in cache update. Multiple threads may overwrite each other's increments.",
                keywords=["race condition", "thread", "concurrent", "lock", "atomic", "synchronization"]
            )
        ],
        hash="bug_006_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Broad exception catch",
        pr_description="Swallow all errors during data import.",
        files_changed=[
            FileChange(
                filename="importer.py",
                patch="""@@ -30,1 +30,2 @@
-    import_data(file)
+    try: import_data(file)
+    except Exception: pass""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_007",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="importer.py",
                line_number=31,
                description="Broad exception catch-all. Swallows all errors including keyboard interrupts.",
                keywords=["exception", "broad", "catch-all", "specific", "silent", "swallow"]
            )
        ],
        hash="bug_007_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Float equality comparison",
        pr_description="Check if sensor reading is exactly 0.1.",
        files_changed=[
            FileChange(
                filename="sensors.py",
                patch="""@@ -7,1 +7,1 @@
-    if reading < 0.1:
+    if reading == 0.1:
+        trigger_alarm()""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_008",
                category=Category.BUG,
                severity=Severity.LOW,
                filename="sensors.py",
                line_number=7,
                description="Floating point equality comparison is unreliable due to precision.",
                keywords=["float", "equality", "precision", "epsilon", "comparison", "IEEE 754"]
            )
        ],
        hash="bug_008_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Return inside finally block",
        pr_description="Override potential errors with a success status.",
        files_changed=[
            FileChange(
                filename="worker.py",
                patch="""@@ -44,1 +44,3 @@
-    process()
+    try: process()
+    finally:
+        return "success" """,
                additions=2,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_009",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="worker.py",
                line_number=46,
                description="Return inside finally block overrides and suppresses exceptions.",
                keywords=["finally", "return", "exception", "control flow", "override", "suppress"]
            )
        ],
        hash="bug_009_h"
    ),
    Scenario(
        task_id=TaskId.BUG_DETECTION,
        pr_title="Type coercion bug",
        pr_description="Compare incoming string ID with integer constant.",
        files_changed=[
            FileChange(
                filename="validator.py",
                patch="""@@ -12,1 +12,1 @@
-    if int(obj_id) == 5:
+    if obj_id == 5:
+        return True""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="bug_010",
                category=Category.BUG,
                severity=Severity.MEDIUM,
                filename="validator.py",
                line_number=12,
                description="Type mismatch: comparing string obj_id with integer 5 will always be False.",
                keywords=["type", "coercion", "comparison", "string", "integer", "implicit"]
            )
        ],
        hash="bug_010_h"
    )
]

# --- SECURITY AUDIT SCENARIOS (10) ---
SECURITY_SCENARIOS = [
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Security: Implement raw SQL query for performance",
        pr_description="Bypassing ORM for a specific complex query to improve performance.",
        files_changed=[
            FileChange(
                filename="db/queries.py",
                patch="""@@ -42,1 +42,1 @@
-    return User.objects.filter(username=name)
+    return User.objects.raw(f"SELECT * FROM users WHERE username = '{name}'")""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_001",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                filename="db/queries.py",
                line_number=42,
                description="SQL injection vulnerability via f-string in raw query. Use parameterized queries.",
                keywords=["SQL injection", "parameterized", "f-string", "raw query", "exploit"]
            )
        ],
        hash="sec_001_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Config: Add development secret key",
        pr_description="Setting a default secret key for local development convenience.",
        files_changed=[
            FileChange(
                filename="settings.py",
                patch="""@@ -20,1 +20,1 @@
-SECRET_KEY = os.environ.get('SECRET_KEY')
+SECRET_KEY = "django-insecure-dev-key-12345" """,
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_002",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                filename="settings.py",
                line_number=20,
                description="Hardcoded secret key in configuration. Should use environment variables.",
                keywords=["hardcoded", "secret", "environment variable", ".env", "credential", "exposure"]
            )
        ],
        hash="sec_002_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="JWT: Disable verification for internal testing",
        pr_description="Allow bypassing JWT checks for faster local development loop.",
        files_changed=[
            FileChange(
                filename="tokens.py",
                patch="""@@ -10,1 +10,1 @@
-    payload = jwt.decode(token, secret, algorithms=["HS256"])
+    payload = jwt.decode(token, verify=False, algorithms=["HS256"])""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_003",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                filename="tokens.py",
                line_number=10,
                description="JWT decoded without verification. Attackers can bypass authentication.",
                keywords=["JWT", "signature", "verification", "algorithm", "none", "bypass"]
            )
        ],
        hash="sec_003_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="XSS: Render user bio directly",
        pr_description="Enabling rich text in user bios by using mark_safe.",
        files_changed=[
            FileChange(
                filename="templates/profile.html",
                patch="""@@ -5,1 +5,1 @@
-    <div class="bio">{{ user.bio }}</div>
+    <div class="bio">{{ user.bio | mark_safe }}</div>""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_004",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                filename="templates/profile.html",
                line_number=5,
                description="Cross-site scripting (XSS) via unescaped template variable. sanitize user input.",
                keywords=["XSS", "cross-site scripting", "mark_safe", "escape", "sanitize", "inject"]
            )
        ],
        hash="sec_004_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="File: Open local logs",
        pr_description="New endpoint to read local audit logs based on path.",
        files_changed=[
            FileChange(
                filename="logs_viewer.py",
                patch="""@@ -12,1 +12,2 @@
 def get_log(path):
-    return open('/var/log/app.log').read()
+    return open('/var/log/' + path).read()""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_005",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                filename="logs_viewer.py",
                line_number=13,
                description="Path traversal vulnerability. Allow reading any file using ../ notation.",
                keywords=["path traversal", "directory", "normalization", "join", "sanitize", "escape"]
            )
        ],
        hash="sec_005_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Serialization: Load user state from pickle",
        pr_description="Faster state loading by using pickle format for internal caches.",
        files_changed=[
            FileChange(
                filename="cache_util.py",
                patch="""@@ -8,1 +8,1 @@
-    return json.loads(data)
+    return pickle.loads(data)""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_006",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                filename="cache_util.py",
                line_number=8,
                description="Insecure deserialization using pickle leads to Arbitrary Code Execution (RCE).",
                keywords=["deserialization", "pickle", "arbitrary code", "RCE", "untrusted", "injection"]
            )
        ],
        hash="sec_006_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="CORS: Allow all origins for API",
        pr_description="Resolving frontend browser errors by allowing all origins.",
        files_changed=[
            FileChange(
                filename="api_gateway.py",
                patch="""@@ -15,1 +15,1 @@
-    allow_origins=["https://myapp.com"],
+    allow_origins=["*"],""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_007",
                category=Category.SECURITY,
                severity=Severity.MEDIUM,
                filename="api_gateway.py",
                line_number=15,
                description="Broad CORS policy (*) allows sensitive data exposure to arbitrary websites.",
                keywords=["CORS", "wildcard", "origin", "cross-origin", "authentication", "header"]
            )
        ],
        hash="sec_007_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Pass: Compare hashes directly",
        pr_description="Faster password check by using native equality.",
        files_changed=[
            FileChange(
                filename="pass_verify.py",
                patch="""@@ -10,1 +10,1 @@
-    return hmac.compare_digest(h1, h2)
+    return h1 == h2""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_008",
                category=Category.SECURITY,
                severity=Severity.MEDIUM,
                filename="pass_verify.py",
                line_number=10,
                description="Timing attack vulnerability in password comparison. Use constant-time comparison.",
                keywords=["timing attack", "constant time", "hmac", "comparison", "side channel"]
            )
        ],
        hash="sec_008_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Auth: Remove login limit",
        pr_description="Allowing multiple login attempts for users who forgot passwords.",
        files_changed=[
            FileChange(
                filename="login_handler.py",
                patch="""@@ -12,1 +12,0 @@
-    if check_rate_limit(ip): return error()""",
                additions=0,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_009",
                category=Category.SECURITY,
                severity=Severity.MEDIUM,
                filename="login_handler.py",
                line_number=12,
                description="Missing rate limiting on login endpoint enables brute-force attacks.",
                keywords=["rate limit", "brute force", "throttle", "attempt", "lockout", "login"]
            )
        ],
        hash="sec_009_h"
    ),
    Scenario(
        task_id=TaskId.SECURITY_AUDIT,
        pr_title="Debug: Enable production stack traces",
        pr_description="Better debugging in prod by enabling stack traces for 500 errors.",
        files_changed=[
            FileChange(
                filename="prod_settings.py",
                patch="""@@ -30,1 +30,1 @@
-DEBUG = False
+DEBUG = True""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="sec_010",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                filename="prod_settings.py",
                line_number=30,
                description="DEBUG mode enabled in production. Exposes sensitive system information.",
                keywords=["debug", "production", "sensitive", "stack trace", "information disclosure"]
            )
        ],
        hash="sec_010_h"
    )
]

# --- ARCHITECTURAL REVIEW SCENARIOS (10) ---
ARCH_SCENARIOS = [
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Refactor: Frontend direct DB access",
        pr_description="Optimizing frontend by allowing direct database reads for dashboard data.",
        files_changed=[
            FileChange(
                filename="services/dashboard.py",
                patch="""@@ -5,1 +5,4 @@
-    return requests.get(API_URL + '/stats').json()
+    import psycopg2
+    conn = psycopg2.connect(DB_URL)
+    cur = conn.cursor()
+    cur.execute('SELECT * FROM stats')
+    return cur.fetchall()""",
                additions=5,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_001",
                category=Category.ARCHITECTURE,
                severity=Severity.CRITICAL,
                filename="services/dashboard.py",
                line_number=5,
                description="Frontend service calling database directly bypassing the API layer. Violates separation of concerns.",
                keywords=["direct access", "coupling", "separation of concerns", "architectural violation"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_001_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Sync: HTTP call inside event handler",
        pr_description="Ensuring user status is verified during login event processing.",
        files_changed=[
            FileChange(
                filename="handlers/events.py",
                patch="""@@ -15,1 +15,2 @@
 def on_user_login(user_id):
-    log.info(f"User {user_id} logged in")
+    resp = requests.get(f"http://auth-service/verify/{user_id}")
+    log.info(f"User {user_id} logged in: {resp.status_code}")""",
                additions=2,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_002",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                filename="handlers/events.py",
                line_number=15,
                description="Synchronous HTTP call inside event handler blocks the event loop.",
                keywords=["synchronous", "blocking", "event loop", "async", "non-blocking", "timeout"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_002_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Reliability: Direct API call without retries",
        pr_description="Call downstream billing service directly.",
        files_changed=[
            FileChange(
                filename="billing_proxy.py",
                patch="""@@ -10,1 +10,1 @@
-    return resiliency.call_with_retry(BILLING_URL)
+    return requests.post(BILLING_URL, data=payload)""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_003",
                category=Category.ARCHITECTURE,
                severity=Severity.MEDIUM,
                filename="billing_proxy.py",
                line_number=10,
                description="Missing retry logic and circuit breaker on external API call.",
                keywords=["retry", "circuit breaker", "resilience", "idempotent", "backoff", "failure"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_003_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Design: Implement GlobalManager",
        pr_description="Consolidating all managers into one for easier access.",
        files_changed=[
            FileChange(
                filename="app_core.py",
                patch="""@@ -1,1 +1,4 @@
-class App: pass
+class GlobalManager:
+    def handle_auth(self): pass
+    def handle_billing(self): pass
+    def handle_users(self): pass""",
                additions=4,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_004",
                category=Category.ARCHITECTURE,
                severity=Severity.MEDIUM,
                filename="app_core.py",
                line_number=2,
                description="God object pattern: one class handles unrelated domains (auth, billing, users).",
                keywords=["single responsibility", "god object", "cohesion", "separation", "refactor"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_004_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Db: Fetch users in loop",
        pr_description="Process audit for all users one by one.",
        files_changed=[
            FileChange(
                filename="audit_job.py",
                patch="""@@ -5,2 +5,2 @@
-    users = User.objects.all().prefetch_related('logs')
-    for u in users: process(u)
+    for u_id in user_ids:
+        user = User.objects.get(id=u_id)
+        process(user)""",
                additions=2,
                deletions=2
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_005",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                filename="audit_job.py",
                line_number=6,
                description="N+1 query problem: fetching user objects inside a loop.",
                keywords=["N+1", "query", "loop", "batch", "eager load", "select_related"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_005_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Api: Get all logs endpoint",
        pr_description="Simple endpoint to fetch current log state.",
        files_changed=[
            FileChange(
                filename="handlers/api.py",
                patch="""@@ -20,1 +20,1 @@
-def get_logs(page, limit): return db.logs.all()[page*limit:(page+1)*limit]
+def get_logs(): return db.logs.all()""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_006",
                category=Category.ARCHITECTURE,
                severity=Severity.MEDIUM,
                filename="handlers/api.py",
                line_number=20,
                description="Missing pagination on endpoint. Can cause memory exhaustion on large datasets.",
                keywords=["pagination", "limit", "offset", "memory", "unbounded", "cursor"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_006_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="File: Upload blocking",
        pr_description="Directly saving large file uploads to disk in request thread.",
        files_changed=[
            FileChange(
                filename="upload_service.py",
                patch="""@@ -12,1 +12,1 @@
-    await background_save(file)
+    file.save('/tmp/large_file')""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_007",
                category=Category.ARCHITECTURE,
                severity=Severity.MEDIUM,
                filename="upload_service.py",
                line_number=13,
                description="Synchronous file upload blocking the request thread. Use background tasks.",
                keywords=["async", "upload", "background task", "streaming", "thread", "non-blocking"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_007_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Payment: Direct mutation",
        pr_description="Update balance directly on payment request.",
        files_changed=[
            FileChange(
                filename="checkout.py",
                patch="""@@ -8,1 +8,1 @@
-    process_payment_with_idempotency(req)
+    user.balance -= req.amount""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_008",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                filename="checkout.py",
                line_number=8,
                description="Missing idempotency key on payment mutation endpoint. Dangerous on retries.",
                keywords=["idempotency", "duplicate", "payment", "retry", "key", "mutation"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_008_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Service: Shared DB state",
        pr_description="Service B updates Service A's table directly for speed.",
        files_changed=[
            FileChange(
                filename="service_b/sync.py",
                patch="""@@ -22,1 +22,1 @@
-    send_event_to_service_a(data)
+    db.execute('UPDATE service_a_table SET x = 1')""",
                additions=1,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_009",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                filename="service_b/sync.py",
                line_number=23,
                description="Shared mutable state between microservices via direct DB write. Breaks encapsulation.",
                keywords=["shared state", "microservice", "event", "eventual consistency", "ownership", "coupling"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_009_h"
    ),
    Scenario(
        task_id=TaskId.ARCHITECTURAL_REVIEW,
        pr_title="Clean: Domain logic in handler",
        pr_description="Complex interest calculation directly in the GET endpoint.",
        files_changed=[
            FileChange(
                filename="api/finance.py",
                patch="""@@ -15,1 +15,3 @@
-    return finance_service.calc_interest(u)
+    interest = u.balance * 0.05
+    if u.type == 'GOLD': interest += 10
+    return interest""",
                additions=3,
                deletions=1
            )
        ],
        ground_truth_issues=[
            GroundTruthIssue(
                id="arch_010",
                category=Category.ARCHITECTURE,
                severity=Severity.MEDIUM,
                filename="api/finance.py",
                line_number=16,
                description="Clean architecture violation: domain logic leaked into HTTP handler.",
                keywords=["clean architecture", "domain", "handler", "concern", "presentation", "business logic"],
                required_verdict=Verdict.REQUEST_CHANGES
            )
        ],
        hash="arch_010_h"
    )
]

SCENARIOS = {
    TaskId.BUG_DETECTION: BUG_SCENARIOS,
    TaskId.SECURITY_AUDIT: SECURITY_SCENARIOS,
    TaskId.ARCHITECTURAL_REVIEW: ARCH_SCENARIOS,
}
