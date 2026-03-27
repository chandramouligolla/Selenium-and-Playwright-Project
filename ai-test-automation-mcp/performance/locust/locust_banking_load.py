"""
Locust Performance Test Suite — Lloyds Banking Group (BFSI)
============================================================
Simulates real-world banking load scenarios:
  - 500+ concurrent users
  - Stress, Spike, and Endurance test scenarios
  - FastAPI microservices load validation
  - SLA compliance checks

Run:
    locust -f locust_banking_load.py --host=https://api.yourbank.com
    locust -f locust_banking_load.py --headless -u 500 -r 50 --run-time 10m
"""

import random
import json
import time
from locust import HttpUser, TaskSet, task, between, events
from locust.exception import RescheduleTask


# ─── Config ───────────────────────────────────────────────────────────────────

BASE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

ACCOUNTS = [f"ACC{str(i).zfill(8)}" for i in range(1, 1001)]
USERS = [{"username": f"user{i}@lloyds.com", "password": "Test@1234"} for i in range(1, 201)]

SLA_THRESHOLDS = {
    "login":            500,   # ms
    "account_balance":  300,
    "transaction_list": 800,
    "fund_transfer":    1000,
    "statement":        1200,
}


# ─── Task Sets ────────────────────────────────────────────────────────────────

class AuthTaskSet(TaskSet):
    """Authentication & session management tasks."""

    def on_start(self):
        self.token = None
        self.login()

    def login(self):
        user = random.choice(USERS)
        with self.client.post(
            "/api/v1/auth/login",
            json=user,
            headers=BASE_HEADERS,
            catch_response=True,
            name="POST /auth/login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
                raise RescheduleTask()

    def get_auth_headers(self):
        return {**BASE_HEADERS, "Authorization": f"Bearer {self.token}"}

    @task(1)
    def logout(self):
        self.client.post(
            "/api/v1/auth/logout",
            headers=self.get_auth_headers(),
            name="POST /auth/logout"
        )
        self.login()


class AccountTaskSet(TaskSet):
    """Account management tasks — high frequency."""

    def on_start(self):
        self.token = self._get_token()
        self.account_id = random.choice(ACCOUNTS)

    def _get_token(self):
        user = random.choice(USERS)
        res = self.client.post("/api/v1/auth/login", json=user, headers=BASE_HEADERS)
        if res.status_code == 200:
            return res.json().get("access_token")
        return ""

    def get_auth_headers(self):
        return {**BASE_HEADERS, "Authorization": f"Bearer {self.token}"}

    @task(5)
    def get_account_balance(self):
        account = random.choice(ACCOUNTS)
        with self.client.get(
            f"/api/v1/accounts/{account}/balance",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="GET /accounts/{id}/balance"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "balance" not in data:
                    response.failure("Missing balance field in response")
                else:
                    elapsed = response.elapsed.total_seconds() * 1000
                    if elapsed > SLA_THRESHOLDS["account_balance"]:
                        response.failure(f"SLA breach: {elapsed:.0f}ms > {SLA_THRESHOLDS['account_balance']}ms")
                    else:
                        response.success()
            elif response.status_code == 404:
                response.success()  # Expected for some accounts
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(4)
    def get_transaction_list(self):
        account = random.choice(ACCOUNTS)
        params = {
            "page": random.randint(1, 5),
            "limit": random.choice([10, 20, 50]),
            "from_date": "2025-01-01",
            "to_date": "2025-12-31"
        }
        with self.client.get(
            f"/api/v1/accounts/{account}/transactions",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="GET /accounts/{id}/transactions"
        ) as response:
            if response.status_code == 200:
                elapsed = response.elapsed.total_seconds() * 1000
                if elapsed > SLA_THRESHOLDS["transaction_list"]:
                    response.failure(f"SLA breach: {elapsed:.0f}ms > {SLA_THRESHOLDS['transaction_list']}ms")
                else:
                    response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def get_account_statement(self):
        account = random.choice(ACCOUNTS)
        with self.client.get(
            f"/api/v1/accounts/{account}/statement",
            params={"month": random.randint(1, 12), "year": 2025},
            headers=self.get_auth_headers(),
            catch_response=True,
            name="GET /accounts/{id}/statement"
        ) as response:
            elapsed = response.elapsed.total_seconds() * 1000
            if response.status_code == 200:
                if elapsed > SLA_THRESHOLDS["statement"]:
                    response.failure(f"SLA breach: {elapsed:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def fund_transfer(self):
        from_acc = random.choice(ACCOUNTS)
        to_acc = random.choice([a for a in ACCOUNTS if a != from_acc])
        payload = {
            "from_account": from_acc,
            "to_account": to_acc,
            "amount": round(random.uniform(10.00, 5000.00), 2),
            "currency": "GBP",
            "reference": f"PERF-TEST-{int(time.time())}",
            "description": "Locust performance test transfer"
        }
        with self.client.post(
            "/api/v1/transfers",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="POST /transfers"
        ) as response:
            elapsed = response.elapsed.total_seconds() * 1000
            if response.status_code in [200, 201, 202]:
                if elapsed > SLA_THRESHOLDS["fund_transfer"]:
                    response.failure(f"SLA breach: {elapsed:.0f}ms > {SLA_THRESHOLDS['fund_transfer']}ms")
                else:
                    response.success()
            elif response.status_code == 422:
                response.success()  # Validation error is expected in perf testing
            else:
                response.failure(f"Transfer failed: {response.status_code}")

    @task(1)
    def get_account_details(self):
        account = random.choice(ACCOUNTS)
        self.client.get(
            f"/api/v1/accounts/{account}",
            headers=self.get_auth_headers(),
            name="GET /accounts/{id}"
        )


class PaymentTaskSet(TaskSet):
    """Payment & standing order tasks."""

    def on_start(self):
        self.token = self._get_token()

    def _get_token(self):
        user = random.choice(USERS)
        res = self.client.post("/api/v1/auth/login", json=user, headers=BASE_HEADERS)
        return res.json().get("access_token") if res.status_code == 200 else ""

    def get_auth_headers(self):
        return {**BASE_HEADERS, "Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_pending_payments(self):
        self.client.get(
            "/api/v1/payments/pending",
            headers=self.get_auth_headers(),
            name="GET /payments/pending"
        )

    @task(2)
    def get_standing_orders(self):
        account = random.choice(ACCOUNTS)
        self.client.get(
            f"/api/v1/accounts/{account}/standing-orders",
            headers=self.get_auth_headers(),
            name="GET /accounts/{id}/standing-orders"
        )

    @task(1)
    def create_payment(self):
        payload = {
            "payee_name": f"Payee_{random.randint(1, 100)}",
            "sort_code": f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
            "account_number": str(random.randint(10000000, 99999999)),
            "amount": round(random.uniform(50.00, 2000.00), 2),
            "payment_date": "2025-12-01",
            "reference": f"PAY-{int(time.time())}"
        }
        self.client.post(
            "/api/v1/payments",
            json=payload,
            headers=self.get_auth_headers(),
            name="POST /payments"
        )


# ─── User Classes ─────────────────────────────────────────────────────────────

class BankingUser(HttpUser):
    """
    Standard banking user — mimics typical retail customer behaviour.
    Weight: 70% of total load.
    """
    tasks = [AccountTaskSet]
    wait_time = between(1, 3)
    weight = 7


class PowerUser(HttpUser):
    """
    Heavy user — business banking customer with frequent transactions.
    Weight: 20% of total load.
    """
    tasks = [AccountTaskSet, PaymentTaskSet]
    wait_time = between(0.5, 1.5)
    weight = 2


class AuthUser(HttpUser):
    """
    Auth-heavy user — simulates session churn (login/logout cycles).
    Weight: 10% of total load.
    """
    tasks = [AuthTaskSet]
    wait_time = between(2, 5)
    weight = 1


# ─── Event Hooks ──────────────────────────────────────────────────────────────

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response,
               context, exception, start_time, url, **kwargs):
    """Log SLA breaches to console for post-test analysis."""
    for endpoint, threshold in SLA_THRESHOLDS.items():
        if endpoint in name.lower() and response_time > threshold:
            print(f"⚠️  SLA BREACH | {name} | {response_time:.0f}ms > {threshold}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("🚀 Locust Banking Load Test Started")
    print(f"   SLA Thresholds: {SLA_THRESHOLDS}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("✅ Locust Banking Load Test Completed")
    stats = environment.stats.total
    print(f"   Total Requests  : {stats.num_requests}")
    print(f"   Failed Requests : {stats.num_failures}")
    print(f"   Avg Response    : {stats.avg_response_time:.0f}ms")
    print(f"   95th Percentile : {stats.get_response_time_percentile(0.95):.0f}ms")
    print(f"   99th Percentile : {stats.get_response_time_percentile(0.99):.0f}ms")
    print("=" * 60)
