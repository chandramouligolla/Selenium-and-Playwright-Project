"""
REST API Test Suite — Banking Accounts & Payments API
PyTest + Playwright Request Context | Contract Testing | Schema Validation
Author: Golla Chandramouli | SDET
"""

import pytest
import requests
from jsonschema import validate, ValidationError
from playwright.sync_api import APIRequestContext, Playwright


# ─── CONFIG ───────────────────────────────────
BASE_URL = "https://api.banking-app.com/v1"
TIMEOUT = 10_000  # 10 seconds


# ─── SCHEMAS ──────────────────────────────────
ACCOUNT_SCHEMA = {
    "type": "object",
    "required": ["account_id", "balance", "currency", "status"],
    "properties": {
        "account_id": {"type": "string"},
        "balance": {"type": "number"},
        "currency": {"type": "string", "enum": ["GBP", "USD", "EUR"]},
        "status": {"type": "string", "enum": ["active", "dormant", "closed"]}
    }
}

PAYMENT_SCHEMA = {
    "type": "object",
    "required": ["transaction_id", "amount", "status", "timestamp"],
    "properties": {
        "transaction_id": {"type": "string"},
        "amount": {"type": "number", "minimum": 0},
        "status": {"type": "string", "enum": ["pending", "completed", "failed", "reversed"]},
        "timestamp": {"type": "string"}
    }
}


# ─── FIXTURES ─────────────────────────────────
@pytest.fixture(scope="session")
def api_context(playwright: Playwright) -> APIRequestContext:
    """Playwright Request Context with auth headers."""
    context = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={
            "Authorization": "Bearer test_token_abc123",
            "Content-Type": "application/json",
            "X-Client-ID": "test-automation"
        }
    )
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def api_context_no_auth(playwright: Playwright) -> APIRequestContext:
    """Unauthenticated context for negative tests."""
    context = playwright.request.new_context(base_url=BASE_URL)
    yield context
    context.dispose()


# ─── ACCOUNT TESTS ────────────────────────────
class TestAccountsAPI:

    @pytest.mark.smoke
    def test_get_account_success(self, api_context: APIRequestContext):
        """GET /accounts/:id — happy path with schema validation."""
        response = api_context.get("/accounts/ACC-001")

        assert response.status == 200
        data = response.json()

        # Contract / Schema validation
        try:
            validate(instance=data, schema=ACCOUNT_SCHEMA)
        except ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")

    @pytest.mark.regression
    def test_get_account_not_found(self, api_context: APIRequestContext):
        """GET /accounts/:id — non-existent account returns 404."""
        response = api_context.get("/accounts/NONEXISTENT-999")
        assert response.status == 404
        assert "error" in response.json()

    @pytest.mark.regression
    def test_get_account_unauthorized(self, api_context_no_auth: APIRequestContext):
        """GET /accounts/:id — without auth token returns 401."""
        response = api_context_no_auth.get("/accounts/ACC-001")
        assert response.status == 401

    @pytest.mark.regression
    def test_account_balance_non_negative(self, api_context: APIRequestContext):
        """BFSI rule: account balance must never be negative for savings accounts."""
        response = api_context.get("/accounts/ACC-001")
        data = response.json()
        if data.get("account_type") == "savings":
            assert data["balance"] >= 0, "Savings account balance cannot be negative"

    @pytest.mark.performance
    def test_get_account_response_time(self, api_context: APIRequestContext):
        """Performance: Account fetch must respond within 2 seconds."""
        import time
        start = time.time()
        response = api_context.get("/accounts/ACC-001")
        elapsed = time.time() - start

        assert response.status == 200
        assert elapsed < 2.0, f"Too slow: {elapsed:.2f}s"


# ─── PAYMENTS TESTS ───────────────────────────
class TestPaymentsAPI:

    @pytest.mark.smoke
    def test_create_payment_success(self, api_context: APIRequestContext):
        """POST /payments — successful domestic transfer."""
        payload = {
            "from_account": "ACC-001",
            "to_account": "ACC-002",
            "amount": 100.00,
            "currency": "GBP",
            "reference": "TEST-PAY-001"
        }
        response = api_context.post("/payments", data=payload)

        assert response.status == 201
        data = response.json()
        validate(instance=data, schema=PAYMENT_SCHEMA)
        assert data["status"] == "pending"

    @pytest.mark.regression
    def test_payment_insufficient_funds(self, api_context: APIRequestContext):
        """BFSI: Payment exceeding balance should return 422."""
        payload = {
            "from_account": "ACC-LOW-BALANCE",
            "to_account": "ACC-002",
            "amount": 999_999.99,
            "currency": "GBP",
            "reference": "TEST-OVERDRAFT"
        }
        response = api_context.post("/payments", data=payload)
        assert response.status == 422
        assert "insufficient" in response.json().get("error", "").lower()

    @pytest.mark.regression
    def test_payment_duplicate_reference(self, api_context: APIRequestContext):
        """Idempotency: Duplicate payment reference should return 409."""
        payload = {
            "from_account": "ACC-001",
            "to_account": "ACC-002",
            "amount": 50.00,
            "currency": "GBP",
            "reference": "DUPLICATE-REF-001"  # Pre-seeded in test DB
        }
        response = api_context.post("/payments", data=payload)
        assert response.status == 409

    @pytest.mark.regression
    def test_payment_invalid_currency(self, api_context: APIRequestContext):
        """Validation: Unsupported currency code should return 400."""
        payload = {
            "from_account": "ACC-001",
            "to_account": "ACC-002",
            "amount": 50.00,
            "currency": "XYZ",
            "reference": "TEST-INVALID-CURR"
        }
        response = api_context.post("/payments", data=payload)
        assert response.status == 400

    @pytest.mark.smoke
    def test_get_payment_status(self, api_context: APIRequestContext):
        """GET /payments/:id — retrieve payment status by transaction ID."""
        response = api_context.get("/payments/TXN-001")
        assert response.status == 200
        data = response.json()
        assert data["status"] in ["pending", "completed", "failed", "reversed"]
