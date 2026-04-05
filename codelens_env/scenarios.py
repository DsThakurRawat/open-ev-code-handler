from codelens_env.models import Scenario, FileChanged, GroundTruthIssue, Category, Severity, TaskId, Verdict

def get_scenario(task_id: TaskId, seed: int) -> Scenario:
    scenarios = [s for s in ALL_SCENARIOS if s.task_id == task_id]
    if not scenarios:
        raise ValueError(f"No scenarios found for task: {task_id}")
    return scenarios[seed % len(scenarios)]

def all_scenarios() -> list[Scenario]:
    return ALL_SCENARIOS

# --- BUG DETECTION SCENARIOS ---

bug_001 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Add pagination to user list endpoint",
    pr_description="Processing elements in the list but missing the last one due to range(len(x)-1).",
    files_changed=[
        FileChanged(
            filename="api/users.py",
            language="python",
            patch="""--- a/api/users.py
+++ b/api/users.py
@@ -10,3 +10,3 @@
 def get_users(page, size):
     items = db.get_all_users()
-    return items[page * size : (page + 1) * size]
+    return items[page * size : page * size + size - 1]""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_001",
            category=Category.BUG,
            severity=Severity.MEDIUM,
            filename="api/users.py",
            line_number=12,
            description="Off-by-one error in pagination slice loses last item per page",
            keywords=["off-by-one", "pagination"]
        )
    ],
    hash="bug_001",
    difficulty="easy"
)

bug_002 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Refactor user profile builder",
    pr_description="New helper to fetch data with a default empty list for items.",
    files_changed=[
        FileChanged(
            filename="models/profile.py",
            language="python",
            patch="""--- a/models/profile.py
+++ b/models/profile.py
@@ -3,3 +3,5 @@
-def build_profile(name, tags=None):
-    tags = tags or []
+def build_profile(name, tags=[]):
+    tags.append("user")
+    return {"name": name, "tags": tags}""",
            additions=3,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_002",
            category=Category.BUG,
            severity=Severity.MEDIUM,
            filename="models/profile.py",
            line_number=5,
            description="Mutable default argument causes state leakage between calls",
            keywords=["mutable", "default"]
        )
    ],
    hash="bug_002",
    difficulty="easy"
)

bug_003 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Add session-based auth check",
    pr_description="Lookup user by ID and access properties without guard.",
    files_changed=[
        FileChanged(
            filename="auth.py",
            language="python",
            patch="""--- a/auth.py
+++ b/auth.py
@@ -14,3 +14,3 @@
 def check_auth(session_id):
     user = get_user(session_id)
-    if user and user.is_active:
+    return user.is_admin""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_003",
            category=Category.BUG,
            severity=Severity.HIGH,
            filename="auth.py",
            line_number=16,
            description="None dereference — get_user can return None, user.is_admin will crash",
            keywords=["None", "dereference"]
        )
    ],
    hash="bug_003",
    difficulty="medium"
)

bug_004 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Add global request counter",
    pr_description="Parallel threads updating shared cache without locking.",
    files_changed=[
        FileChanged(
            filename="middleware/counter.py",
            language="python",
            patch="""--- a/middleware/counter.py
+++ b/middleware/counter.py
@@ -5,3 +5,3 @@
-def increment():
-    with lock:
-        global count
-        count += 1
+def increment():
+    global count
+    count += 1""",
            additions=2,
            deletions=3,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_004",
            category=Category.BUG,
            severity=Severity.HIGH,
            filename="middleware/counter.py",
            line_number=7,
            description="Race condition in counter update: multiple threads may overwrite each other's increments.",
            keywords=["race condition", "thread"]
        )
    ],
    hash="bug_004",
    difficulty="hard"
)

bug_005 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Handle DB connection errors",
    pr_description="Swallow all errors during data import.",
    files_changed=[
        FileChanged(
            filename="db/connection.py",
            language="python",
            patch="""--- a/db/connection.py
+++ b/db/connection.py
@@ -8,3 +8,3 @@
-    except psycopg2.OperationalError:
-        log.error("DB down")
+    except Exception:
+        pass""",
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_005",
            category=Category.BUG,
            severity=Severity.MEDIUM,
            filename="db/connection.py",
            line_number=9,
            description="Broad exception catch-all suppresses real errors and hides bugs.",
            keywords=["broad exception", "catch"]
        )
    ],
    hash="bug_005",
    difficulty="medium"
)

bug_006 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Add score percentage calculator",
    pr_description="Integer division result truncated.",
    files_changed=[
        FileChanged(
            filename="scoring/calc.py",
            language="python",
            patch="""--- a/scoring/calc.py
+++ b/scoring/calc.py
@@ -4,3 +4,3 @@
 def get_percentage(score, total):
-    return (score / total) * 100
+    return score / total""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_006",
            category=Category.BUG,
            severity=Severity.LOW,
            filename="scoring/calc.py",
            line_number=5,
            description="Integer division truncation or missing multiplier in percentage calculation",
            keywords=["division", "truncat"]
        )
    ],
    hash="bug_006",
    difficulty="medium"
)

bug_007 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Simplify status checker",
    pr_description="Unreachable code after return.",
    files_changed=[
        FileChanged(
            filename="utils/status.py",
            language="python",
            patch="""--- a/utils/status.py
+++ b/utils/status.py
@@ -5,5 +5,3 @@
 def is_active(user):
-    if user.deleted:
-        return False
-    return user.active
+    return True
+    log.info("Checked user status")""",
            additions=2,
            deletions=3,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_007",
            category=Category.BUG,
            severity=Severity.LOW,
            filename="utils/status.py",
            line_number=8,
            description="Unreachable code after return statement",
            keywords=["unreachable", "dead code"]
        )
    ],
    hash="bug_007",
    difficulty="medium"
)

bug_008 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Parse webhook payload",
    pr_description="Dict key assumed present — will KeyError if user absent.",
    files_changed=[
        FileChanged(
            filename="webhooks/parser.py",
            language="python",
            patch="""--- a/webhooks/parser.py
+++ b/webhooks/parser.py
@@ -12,2 +12,2 @@
 def parse_event(data):
-    email = data.get("user", {}).get("email")
+    email = data["user"]["email"]""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_008",
            category=Category.BUG,
            severity=Severity.HIGH,
            filename="webhooks/parser.py",
            line_number=13,
            description="Unsafe dictionary access will raise KeyError if 'user' or 'email' keys are missing",
            keywords=["KeyError", "dict"]
        )
    ],
    hash="bug_008",
    difficulty="medium"
)

bug_009 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Add balance check to payment flow",
    pr_description="Check if sensor reading is exactly 0.0.",
    files_changed=[
        FileChanged(
            filename="payments/validator.py",
            language="python",
            patch="""--- a/payments/validator.py
+++ b/payments/validator.py
@@ -7,3 +7,3 @@
 def validate_tx(balance, amount):
-    if balance < 0.01:
+    if balance == 0.0:
         return False""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_009",
            category=Category.BUG,
            severity=Severity.MEDIUM,
            filename="payments/validator.py",
            line_number=8,
            description="Floating point equality comparison is unreliable due to precision issues",
            keywords=["float", "comparison"]
        )
    ],
    hash="bug_009",
    difficulty="medium"
)

bug_010 = Scenario(
    task_id=TaskId.BUG_DETECTION,
    pr_title="Clone user config before mutation",
    pr_description="Shallow copy treated as deep copy — affects original.",
    files_changed=[
        FileChanged(
            filename="config/user_config.py",
            language="python",
            patch="""--- a/config/user_config.py
+++ b/config/user_config.py
@@ -10,3 +10,3 @@
 def update_config(original):
-    import copy
-    cfg = copy.deepcopy(original)
+    cfg = original.copy()
+    cfg["settings"]["theme"] = "dark" """,
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="bug_010",
            category=Category.BUG,
            severity=Severity.MEDIUM,
            filename="config/user_config.py",
            line_number=11,
            description="Shallow copy used for nested dictionary mutation; will modify the original object",
            keywords=["shallow copy", "deep copy"]
        )
    ],
    hash="bug_010",
    difficulty="medium"
)

# --- SECURITY AUDIT SCENARIOS ---

sec_001 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add user search endpoint",
    pr_description="Bypassing ORM for a raw SQL query.",
    files_changed=[
        FileChanged(
            filename="api/search.py",
            language="python",
            patch="""--- a/api/search.py
+++ b/api/search.py
@@ -15,3 +15,3 @@
 def find_user(name):
-    return db.users.filter(name=name).first()
+    query = f"SELECT * FROM users WHERE name = '{name}'"
+    return db.execute_raw(query)""",
            additions=2,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_001",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            filename="api/search.py",
            line_number=16,
            description="SQL injection vulnerability via f-string in raw query. Use parameterized queries.",
            keywords=["SQL injection", "injection"]
        )
    ],
    hash="sec_001",
    difficulty="hard"
)

sec_002 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add Stripe webhook handler",
    pr_description="Hardcoded secret key in configuration.",
    files_changed=[
        FileChanged(
            filename="payments/webhook.py",
            language="python",
            patch="""--- a/payments/webhook.py
+++ b/payments/webhook.py
@@ -5,1 +5,1 @@
-stripe_secret = os.getenv("STRIPE_SECRET")
+SECRET_KEY = "sk_live_dummy_secret_key_for_testing_12345" """,
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_002",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            filename="payments/webhook.py",
            line_number=5,
            description="Hardcoded sensitive credentials in source code",
            keywords=["hardcoded", "secret"]
        )
    ],
    hash="sec_002",
    difficulty="easy"
)

sec_003 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add file download endpoint",
    pr_description="New endpoint to read local audit logs based on path (no sanitization).",
    files_changed=[
        FileChanged(
            filename="api/files.py",
            language="python",
            patch="""--- a/api/files.py
+++ b/api/files.py
@@ -10,3 +10,3 @@
 def download_file(user_input):
-    safe_path = os.path.join(BASE_DIR, os.path.basename(user_input))
-    return open(safe_path, "rb").read()
+    filepath = BASE_DIR + "/" + user_input
+    return open(filepath, "rb").read()""",
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_003",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            filename="api/files.py",
            line_number=11,
            description="Path traversal vulnerability: user input is directly concatenated to the base path",
            keywords=["path traversal", "directory traversal"]
        )
    ],
    hash="sec_003",
    difficulty="medium"
)

sec_004 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add system ping utility",
    pr_description="Command injection using os.system with user input.",
    files_changed=[
        FileChanged(
            filename="utils/network.py",
            language="python",
            patch="""--- a/utils/network.py
+++ b/utils/network.py
@@ -8,3 +8,3 @@
 def ping_host(host):
-    import subprocess
-    return subprocess.run(["ping", "-c", "1", host])
+    import os
+    os.system(f"ping -c 1 {host}")""",
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_004",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            filename="utils/network.py",
            line_number=10,
            description="Command injection vulnerability via os.system and shell formatting",
            keywords=["command injection", "os.system"]
        )
    ],
    hash="sec_004",
    difficulty="medium"
)

sec_005 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add session state caching",
    pr_description="Faster state loading by using pickle format for internal caches.",
    files_changed=[
        FileChanged(
            filename="cache/session.py",
            language="python",
            patch="""--- a/cache/session.py
+++ b/cache/session.py
@@ -10,3 +10,3 @@
 def get_session(key):
-    data = redis.get(key)
-    return json.loads(data)
+    import pickle
+    return pickle.loads(redis.get(key))""",
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_005",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            filename="cache/session.py",
            line_number=12,
            description="Insecure deserialization using pickle leads to Arbitrary Code Execution (RCE)",
            keywords=["pickle", "deserialization"]
        )
    ],
    hash="sec_005",
    difficulty="medium"
)

sec_006 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add JWT decode helper",
    pr_description="Allow bypassing JWT checks for faster local development loop.",
    files_changed=[
        FileChanged(
            filename="auth/jwt_helper.py",
            language="python",
            patch="""--- a/auth/jwt_helper.py
+++ b/auth/jwt_helper.py
@@ -15,3 +15,3 @@
 def decode_token(token):
-    return jwt.decode(token, SECRET, algorithms=["HS256"])
+    return jwt.decode(token, options={"verify_signature": False})""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_006",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            filename="auth/jwt_helper.py",
            line_number=16,
            description="JWT decoded without signature verification; attackers can forge any account",
            keywords=["JWT", "signature"]
        )
    ],
    hash="sec_006",
    difficulty="hard"
)

sec_007 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add login redirect",
    pr_description="Allow all origins for login redirect.",
    files_changed=[
        FileChanged(
            filename="views/auth.py",
            language="python",
            patch="""--- a/views/auth.py
+++ b/views/auth.py
@@ -20,3 +20,3 @@
 def login_complete(request):
-    next_url = validate_internal_url(request.args.get("next"))
-    return redirect(next_url or "/dashboard")
+    return redirect(request.args.get("next"))""",
            additions=1,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_007",
            category=Category.SECURITY,
            severity=Severity.MEDIUM,
            filename="views/auth.py",
            line_number=21,
            description="Open redirect vulnerability allows attackers to phish users",
            keywords=["open redirect", "redirect"]
        )
    ],
    hash="sec_007",
    difficulty="medium"
)

sec_008 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Update app configuration",
    pr_description="DEBUG mode enabled in production settings.",
    files_changed=[
        FileChanged(
            filename="config/settings.py",
            language="python",
            patch="""--- a/config/settings.py
+++ b/config/settings.py
@@ -35,3 +35,4 @@
-# Production settings
-DEBUG = False
-TESTING = False
+# Debug settings for prod troubleshooting
+DEBUG = True
+TESTING = True""",
            additions=3,
            deletions=3,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_008",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            filename="config/settings.py",
            line_number=37,
            description="DEBUG mode enabled in production settings discloses system secrets",
            keywords=["debug", "production"]
        )
    ],
    hash="sec_008",
    difficulty="easy"
)

sec_009 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Enable CORS for frontend",
    pr_description="Resolving frontend browser errors by allowing all origins.",
    files_changed=[
        FileChanged(
            filename="app.py",
            language="python",
            patch="""--- a/app.py
+++ b/app.py
@@ -55,3 +55,3 @@
     app.add_middleware(CORSMiddleware, 
-        allow_origins=["https://secure.app.com"],
+        allow_origins=["*"],
         allow_credentials=True)""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_009",
            category=Category.SECURITY,
            severity=Severity.MEDIUM,
            filename="app.py",
            line_number=56,
            description="Sensitive CORS policy with wildcard (*) allows data theft via CSRF",
            keywords=["CORS", "wildcard"]
        )
    ],
    hash="sec_009",
    difficulty="medium"
)

sec_010 = Scenario(
    task_id=TaskId.SECURITY_AUDIT,
    pr_title="Add admin password check",
    pr_description="Faster password check by using native equality.",
    files_changed=[
        FileChanged(
            filename="admin/auth.py",
            language="python",
            patch="""--- a/admin/auth.py
+++ b/admin/auth.py
@@ -10,3 +10,3 @@
 def verify_admin(provided_password):
-    import secrets
-    return secrets.compare_digest(ADMIN_PASS, provided_password)
+    return ADMIN_PASS == provided_password""",
            additions=1,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="sec_010",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            filename="admin/auth.py",
            line_number=11,
            description="Timing attack vulnerability in password comparison; use secrets.compare_digest",
            keywords=["timing attack", "constant time"]
        )
    ],
    hash="sec_010",
    difficulty="medium"
)

# --- ARCHITECTURAL REVIEW SCENARIOS ---

arch_001 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add UserManager service",
    pr_description="A 200-line class that handles auth, email sending, billing, and profile.",
    files_changed=[
        FileChanged(
            filename="services/user_manager.py",
            language="python",
            patch="""--- a/services/user_manager.py
+++ b/services/user_manager.py
@@ -1,5 +1,10 @@
-class UserAuth: pass
-class UserBilling: pass
-class UserEmail: pass
+class UserManager:
+    def authenticate(self, user): pass
+    def process_payment(self, amount): pass
+    def send_welcome_email(self, email): pass
+    def update_profile_picture(self, img): pass
+    def sync_to_marketing_tool(self): pass""",
            additions=6,
            deletions=3,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_001",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="services/user_manager.py",
            line_number=2,
            description="God class violation: UserManager handles multiple unrelated domains (auth, billing, email)",
            keywords=["single responsibility", "god class"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_001",
    difficulty="medium"
)

arch_002 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add order details endpoint",
    pr_description="Fetching order items inside a loop (N+1 query).",
    files_changed=[
        FileChanged(
            filename="api/orders.py",
            language="python",
            patch="""--- a/api/orders.py
+++ b/api/orders.py
@@ -25,3 +25,4 @@
 def get_order_history(user_id):
-    return db.query(Order).options(joinedload(Order.items)).all()
+    orders = db.query(Order).filter_by(user_id=user_id).all()
+    for o in orders:
+        o.items = db.query(Item).filter_by(order_id=o.id).all()
+    return orders""",
            additions=3,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_002",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="api/orders.py",
            line_number=27,
            description="N+1 query pattern: fetching items in a loop will cause DB performance collapse",
            keywords=["N+1", "query"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_002",
    difficulty="hard"
)

arch_003 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add notification system",
    pr_description="Tight coupling via hardwired SendGrid import.",
    files_changed=[
        FileChanged(
            filename="services/notifier.py",
            language="python",
            patch="""--- a/services/notifier.py
+++ b/services/notifier.py
@@ -1,3 +1,3 @@
-from services.interfaces import MailProvider
+from integrations.sendgrid import send_email
 
-def notify(user, provider: MailProvider):
-    provider.send(user.email)
+def notify(user):
+    send_email(user.email)""",
            additions=3,
            deletions=3,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_003",
            category=Category.ARCHITECTURE,
            severity=Severity.MEDIUM,
            filename="services/notifier.py",
            line_number=2,
            description="Tight coupling: service depends on concrete implementation instead of abstraction",
            keywords=["tight coupling", "dependency injection"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_003",
    difficulty="medium"
)

arch_004 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add external price fetch to checkout",
    pr_description="Synchronous blocking call inside async checkout handler.",
    files_changed=[
        FileChanged(
            filename="checkout/handler.py",
            language="python",
            patch="""--- a/checkout/handler.py
+++ b/checkout/handler.py
@@ -10,3 +10,4 @@
 async def checkout(cart):
-    async with aiohttp.ClientSession() as s:
-        price = await s.get(PRICE_API)
+    import requests
+    price = requests.get(PRICE_API)
+    return process_order(price)""",
            additions=2,
            deletions=2,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_004",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="checkout/handler.py",
            line_number=12,
            description="Blocking HTTP call inside async function will stall the entire event loop",
            keywords=["blocking", "async"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_004",
    difficulty="medium"
)

arch_005 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Integrate weather API",
    pr_description="Missing retry/resilience on external call.",
    files_changed=[
        FileChanged(
            filename="services/weather.py",
            language="python",
            patch="""--- a/services/weather.py
+++ b/services/weather.py
@@ -5,3 +5,3 @@
 def get_temp(city):
-    return circuit_breaker.call(WEATHER_URL, timeout=2)
+    return requests.get(WEATHER_URL).json()""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_005",
            category=Category.ARCHITECTURE,
            severity=Severity.MEDIUM,
            filename="services/weather.py",
            line_number=6,
            description="Missing resilience (retry, timeout, circuit breaker) on external API dependency",
            keywords=["retry", "resilience"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_005",
    difficulty="medium"
)

arch_006 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Refactor model relationships",
    pr_description="Circular import between User and Order models.",
    files_changed=[
        FileChanged(
            filename="models/order.py",
            language="python",
            patch="""--- a/models/order.py
+++ b/models/order.py
@@ -1,1 +1,2 @@
+from models.user import User
 class Order(BaseModel):
-    user_id: int
+    user: User""",
            additions=2,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_006",
            category=Category.ARCHITECTURE,
            severity=Severity.MEDIUM,
            filename="models/order.py",
            line_number=1,
            description="Circular dependency risk: order depends on user while user likely imports order",
            keywords=["circular import", "circular dependency"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_006",
    difficulty="hard"
)

arch_007 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add all-products endpoint",
    pr_description="Missing pagination on unbounded list endpoint.",
    files_changed=[
        FileChanged(
            filename="api/products.py",
            language="python",
            patch="""--- a/api/products.py
+++ b/api/products.py
@@ -10,3 +10,3 @@
 def list_products():
-    return db.query(Product).limit(50).all()
+    return db.query(Product).all()""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_007",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="api/products.py",
            line_number=11,
            description="Missing pagination on list endpoint will lead to memory exhaustion",
            keywords=["pagination", "limit"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_007",
    difficulty="medium"
)

arch_008 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Document the payment integration",
    pr_description="Sensitive API key included in documentation comment.",
    files_changed=[
        FileChanged(
            filename="docs/payment_notes.py",
            language="python",
            patch="""--- a/docs/payment_notes.py
+++ b/docs/payment_notes.py
@@ -1,2 +1,3 @@
 # Payment integration notes
+# Use API key: pk_test_abc123 for testing
 def init(): pass""",
            additions=1,
            deletions=0,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_008",
            category=Category.ARCHITECTURE,
            severity=Severity.MEDIUM,
            filename="docs/payment_notes.py",
            line_number=2,
            description="Secret leaked in code comment; should be in environment variables only",
            keywords=["secret", "comment"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_008",
    difficulty="medium"
)

arch_009 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Add detailed auth logging",
    pr_description="Logging sensitive user password in cleartext.",
    files_changed=[
        FileChanged(
            filename="auth/logger.py",
            language="python",
            patch="""--- a/auth/logger.py
+++ b/auth/logger.py
@@ -5,3 +5,3 @@
 def log_login(email, password):
-    logger.info(f"Attempt for {email}")
+    logger.info(f"Login attempt: user={email} password={password}")""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_009",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="auth/logger.py",
            line_number=6,
            description="PII/Security Leak: logging plain-text passwords violates security policy",
            keywords=["sensitive", "log"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_009",
    difficulty="medium"
)

arch_010 = Scenario(
    task_id=TaskId.ARCHITECTURAL_REVIEW,
    pr_title="Set up database connection",
    pr_description="Hardcoded DB connection string with credentials.",
    files_changed=[
        FileChanged(
            filename="db/setup.py",
            language="python",
            patch="""--- a/db/setup.py
+++ b/db/setup.py
@@ -5,3 +5,3 @@
 def connect():
-    url = os.environ.get("DATABASE_URL")
+    url = "postgresql://admin:password123@localhost:5432/mydb"
     return create_engine(url)""",
            additions=1,
            deletions=1,
        )
    ],
    ground_truth_issues=[
        GroundTruthIssue(
            id="arch_010",
            category=Category.ARCHITECTURE,
            severity=Severity.HIGH,
            filename="db/setup.py",
            line_number=6,
            description="Hardcoded environment configuration and credentials",
            keywords=["hardcoded", "configuration"],
            required_verdict=Verdict.REQUEST_CHANGES
        )
    ],
    hash="arch_010",
    difficulty="medium"
)

ALL_SCENARIOS = [
    bug_001, bug_003, bug_002, bug_004, bug_005, bug_006, bug_007, bug_008, bug_009, bug_010,
    sec_001, sec_002, sec_003, sec_004, sec_005, sec_006, sec_007, sec_008, sec_009, sec_010,
    arch_001, arch_002, arch_003, arch_004, arch_005, arch_006, arch_007, arch_008, arch_009, arch_010
]
