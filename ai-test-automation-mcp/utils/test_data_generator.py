"""
GDPR-Compliant Test Data Generator
Faker Engine | Banking Domain | Synthetic Data
Author: Golla Chandramouli | SDET
"""

import random
import string
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from faker import Faker

fake = Faker("en_GB")  # UK locale for Lloyds Banking domain


# ─── DATA MODELS ──────────────────────────────
@dataclass
class BankingCustomer:
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    sort_code: str
    account_number: str
    balance: float
    account_type: str
    created_at: str
    is_gdpr_compliant: bool = True  # Always True — synthetic data only


@dataclass
class PaymentTransaction:
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    currency: str
    reference: str
    status: str
    timestamp: str


# ─── GENERATOR ────────────────────────────────
class BankingTestDataGenerator:
    """
    Generates GDPR-compliant synthetic banking test data.
    No real PII — all data is fully fabricated.

    Usage:
        generator = BankingTestDataGenerator()
        customer = generator.create_customer()
        payment = generator.create_payment(from_account=customer.account_number)
    """

    ACCOUNT_TYPES = ["current", "savings", "isa", "business"]
    CURRENCIES = ["GBP", "USD", "EUR"]
    PAYMENT_STATUSES = ["pending", "completed", "failed", "reversed"]

    def __init__(self, seed: Optional[int] = None):
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        self.fake = Faker("en_GB")

    def _generate_sort_code(self) -> str:
        """Generate UK-format sort code: XX-XX-XX"""
        return "-".join([f"{random.randint(10, 99)}" for _ in range(3)])

    def _generate_account_number(self) -> str:
        """Generate 8-digit UK account number."""
        return "".join([str(random.randint(0, 9)) for _ in range(8)])

    def _generate_transaction_id(self) -> str:
        """Generate transaction ID in TXN-XXXXXX format."""
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"TXN-{suffix}"

    def create_customer(
        self,
        account_type: Optional[str] = None,
        balance: Optional[float] = None,
        locked: bool = False
    ) -> BankingCustomer:
        """Create a synthetic banking customer."""
        first = self.fake.first_name()
        last = self.fake.last_name()
        email_prefix = f"{first.lower()}.{last.lower()}"
        email = f"{email_prefix}{''.join(random.choices(string.digits, k=3))}@synth-bank.test"

        return BankingCustomer(
            customer_id=f"CUST-{self.fake.uuid4()[:8].upper()}",
            first_name=first,
            last_name=last,
            email=email,
            phone=self.fake.phone_number(),
            sort_code=self._generate_sort_code(),
            account_number=self._generate_account_number(),
            balance=balance if balance is not None else round(random.uniform(100, 50_000), 2),
            account_type=account_type or random.choice(self.ACCOUNT_TYPES),
            created_at=self.fake.date_time_between(
                start_date="-5y", end_date="now"
            ).isoformat(),
        )

    def create_payment(
        self,
        from_account: Optional[str] = None,
        to_account: Optional[str] = None,
        amount: Optional[float] = None,
        currency: str = "GBP",
        status: str = "completed"
    ) -> PaymentTransaction:
        """Create a synthetic payment transaction."""
        return PaymentTransaction(
            transaction_id=self._generate_transaction_id(),
            from_account=from_account or self._generate_account_number(),
            to_account=to_account or self._generate_account_number(),
            amount=amount if amount is not None else round(random.uniform(1, 5_000), 2),
            currency=currency,
            reference=f"REF-{self.fake.uuid4()[:6].upper()}",
            status=status,
            timestamp=datetime.utcnow().isoformat()
        )

    def bulk_create_customers(self, count: int) -> list[BankingCustomer]:
        """Generate bulk test customers — for QA team self-service data requests."""
        return [self.create_customer() for _ in range(count)]

    def bulk_create_payments(self, count: int, from_account: str) -> list[PaymentTransaction]:
        """Generate bulk transactions for a given account."""
        return [self.create_payment(from_account=from_account) for _ in range(count)]

    def create_edge_case_customers(self) -> list[BankingCustomer]:
        """Generate pre-defined edge case customers for regression testing."""
        return [
            self.create_customer(account_type="savings", balance=0.00),      # Zero balance
            self.create_customer(account_type="current", balance=0.01),      # Near-zero balance
            self.create_customer(account_type="isa", balance=999_999.99),    # Max balance
            self.create_customer(account_type="business", balance=50_000.0), # Business account
        ]


# ─── PYTEST FIXTURES ──────────────────────────
import pytest

@pytest.fixture(scope="session")
def data_generator():
    return BankingTestDataGenerator(seed=42)  # Seeded for reproducibility


@pytest.fixture
def test_customer(data_generator):
    return data_generator.create_customer()


@pytest.fixture
def test_payment(data_generator, test_customer):
    return data_generator.create_payment(from_account=test_customer.account_number)


@pytest.fixture
def bulk_customers(data_generator):
    return data_generator.bulk_create_customers(10)


# ─── DEMO ─────────────────────────────────────
if __name__ == "__main__":
    gen = BankingTestDataGenerator(seed=42)

    print("=== Sample Customer ===")
    customer = gen.create_customer()
    print(f"  Name:    {customer.first_name} {customer.last_name}")
    print(f"  Email:   {customer.email}")
    print(f"  Account: {customer.sort_code} | {customer.account_number}")
    print(f"  Balance: £{customer.balance:,.2f}")
    print(f"  GDPR OK: {customer.is_gdpr_compliant}")

    print("\n=== Sample Payment ===")
    payment = gen.create_payment(from_account=customer.account_number)
    print(f"  TXN ID: {payment.transaction_id}")
    print(f"  Amount: {payment.currency} {payment.amount}")
    print(f"  Status: {payment.status}")
