"""
DB Assertion Suite — Oracle / PostgreSQL / IBM DB2
=====================================================
End-to-end database validation tests for BFSI workflows.
Validates data integrity across all three databases after
UI and API operations.

Run:
    pytest tests/db/test_db_assertions.py -v --alluredir=reports/allure-results
"""

import pytest
import allure
from datetime import datetime, timedelta
from utils.db_connector import OracleConnector, PostgresConnector, DB2Connector


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def oracle_db():
    conn = OracleConnector()
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture(scope="module")
def postgres_db():
    conn = PostgresConnector()
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture(scope="module")
def db2_db():
    conn = DB2Connector()
    conn.connect()
    yield conn
    conn.disconnect()


# ─── Oracle Tests ─────────────────────────────────────────────────────────────

@allure.feature("DB Assertions")
@allure.story("Oracle — Account Validation")
class TestOracleAssertions:

    @allure.title("Verify account balance updated after fund transfer")
    def test_account_balance_updated_after_transfer(self, oracle_db):
        account_id = "ACC00000001"
        result = oracle_db.execute_query(
            "SELECT balance, last_updated FROM accounts WHERE account_id = :id",
            {"id": account_id}
        )
        assert result, f"No record found for account {account_id}"
        balance, last_updated = result[0]
        assert balance >= 0, "Balance should not be negative"
        assert last_updated.date() == datetime.today().date(), "Last updated date mismatch"

    @allure.title("Verify transaction record inserted after transfer")
    def test_transaction_record_inserted(self, oracle_db):
        result = oracle_db.execute_query(
            """SELECT COUNT(*) FROM transactions
               WHERE created_at >= SYSDATE - 1/24
               AND status = 'COMPLETED'"""
        )
        count = result[0][0]
        assert count > 0, "No recent completed transactions found"

    @allure.title("Verify audit log entry created for login")
    def test_audit_log_entry_for_login(self, oracle_db):
        result = oracle_db.execute_query(
            """SELECT COUNT(*) FROM audit_logs
               WHERE event_type = 'LOGIN'
               AND created_at >= SYSDATE - 1/24"""
        )
        count = result[0][0]
        assert count > 0, "No recent login audit entries found"

    @allure.title("Verify no duplicate transactions exist")
    def test_no_duplicate_transactions(self, oracle_db):
        result = oracle_db.execute_query(
            """SELECT reference_no, COUNT(*) as cnt
               FROM transactions
               GROUP BY reference_no
               HAVING COUNT(*) > 1"""
        )
        assert len(result) == 0, f"Duplicate transactions found: {result}"


# ─── PostgreSQL Tests ──────────────────────────────────────────────────────────

@allure.feature("DB Assertions")
@allure.story("PostgreSQL — User & Session Validation")
class TestPostgresAssertions:

    @allure.title("Verify user session created after login")
    def test_user_session_created(self, postgres_db):
        result = postgres_db.execute_query(
            """SELECT COUNT(*) FROM user_sessions
               WHERE created_at >= NOW() - INTERVAL '1 hour'
               AND is_active = true"""
        )
        count = result[0][0]
        assert count > 0, "No active sessions found in last hour"

    @allure.title("Verify payment record persisted correctly")
    def test_payment_record_persisted(self, postgres_db):
        result = postgres_db.execute_query(
            """SELECT payment_id, amount, status, created_at
               FROM payments
               WHERE created_at >= NOW() - INTERVAL '24 hours'
               ORDER BY created_at DESC
               LIMIT 1"""
        )
        assert result, "No recent payment records found"
        payment_id, amount, status, created_at = result[0]
        assert payment_id is not None
        assert amount > 0
        assert status in ["PENDING", "COMPLETED", "PROCESSING"]

    @allure.title("Verify standing order data integrity")
    def test_standing_order_integrity(self, postgres_db):
        result = postgres_db.execute_query(
            """SELECT COUNT(*) FROM standing_orders
               WHERE next_payment_date < NOW()
               AND status = 'ACTIVE'"""
        )
        overdue = result[0][0]
        assert overdue == 0, f"{overdue} standing orders are overdue and still active"


# ─── IBM DB2 Tests ────────────────────────────────────────────────────────────

@allure.feature("DB Assertions")
@allure.story("IBM DB2 — Transaction & Statement Validation")
class TestDB2Assertions:

    @allure.title("Verify statement record generated correctly")
    def test_statement_record_generated(self, db2_db):
        result = db2_db.execute_query(
            """SELECT COUNT(*) FROM STATEMENTS
               WHERE STATEMENT_DATE >= CURRENT DATE - 30 DAYS"""
        )
        count = result[0][0]
        assert count > 0, "No statements generated in last 30 days"

    @allure.title("Verify transaction amount matches ledger")
    def test_transaction_amount_matches_ledger(self, db2_db):
        result = db2_db.execute_query(
            """SELECT T.AMOUNT, L.DEBIT_AMOUNT
               FROM TRANSACTIONS T
               JOIN LEDGER L ON T.TRANSACTION_ID = L.TRANSACTION_REF
               WHERE T.STATUS = 'COMPLETED'
               FETCH FIRST 10 ROWS ONLY"""
        )
        for amount, debit_amount in result:
            assert abs(float(amount) - float(debit_amount)) < 0.01, \
                f"Amount mismatch: transaction={amount}, ledger={debit_amount}"

    @allure.title("Verify GDPR-compliant data masking in statements")
    def test_gdpr_data_masking(self, db2_db):
        result = db2_db.execute_query(
            """SELECT ACCOUNT_NUMBER FROM STATEMENTS
               FETCH FIRST 5 ROWS ONLY"""
        )
        for (account_number,) in result:
            visible_digits = account_number.replace("*", "").replace("X", "")
            assert len(visible_digits) <= 4, \
                f"Account number not properly masked: {account_number}"
