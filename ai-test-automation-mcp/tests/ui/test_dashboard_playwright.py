"""
Playwright UI Test Suite — Banking Login & Dashboard
Page Object Model (POM) pattern | BFSI Domain
Author: Golla Chandramouli | SDET
"""

import pytest
from playwright.sync_api import Page, expect


class LoginPage:
    """Page Object for Login Page."""

    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator("#username")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("[data-testid='login-btn']")
        self.error_message = page.locator(".error-banner")
        self.otp_field = page.locator("#otp-input")

    def navigate(self, base_url: str):
        self.page.goto(f"{base_url}/auth/login")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def submit_otp(self, otp: str):
        self.otp_field.fill(otp)
        self.page.locator("[data-testid='verify-otp-btn']").click()

    def get_error_message(self) -> str:
        return self.error_message.inner_text()


class DashboardPage:
    """Page Object for Dashboard Page."""

    def __init__(self, page: Page):
        self.page = page
        self.welcome_banner = page.locator(".welcome-banner")
        self.account_balance = page.locator("[data-testid='account-balance']")
        self.nav_menu = page.locator(".nav-menu")

    def is_loaded(self) -> bool:
        return self.welcome_banner.is_visible()


# ─────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────

BASE_URL = "https://demo.banking-app.com"  # Replace with actual URL


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    lp = LoginPage(page)
    lp.navigate(BASE_URL)
    return lp


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    return DashboardPage(page)


@pytest.mark.smoke
class TestLoginSmoke:

    def test_login_page_loads(self, login_page: LoginPage):
        """Verify login page loads with all key elements."""
        expect(login_page.username_input).to_be_visible()
        expect(login_page.password_input).to_be_visible()
        expect(login_page.login_button).to_be_enabled()

    def test_successful_login(self, login_page: LoginPage, page: Page):
        """Happy path: valid credentials should redirect to dashboard."""
        login_page.login("valid_user@bank.com", "SecurePass@123")
        expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=10_000)

    def test_login_page_title(self, page: Page, login_page: LoginPage):
        """Page title should match branding."""
        expect(page).to_have_title("Secure Banking Login")


@pytest.mark.regression
class TestLoginNegative:

    def test_invalid_password(self, login_page: LoginPage):
        """Negative: wrong password should show error, not crash."""
        login_page.login("valid_user@bank.com", "WrongPassword!")
        error = login_page.get_error_message()
        assert "Invalid credentials" in error

    def test_empty_credentials(self, login_page: LoginPage):
        """Boundary: empty fields should prevent form submission."""
        login_page.login_button.click()
        expect(login_page.username_input).to_have_attribute("aria-invalid", "true")

    def test_sql_injection_attempt(self, login_page: LoginPage):
        """Security: SQL injection in username should be rejected safely."""
        login_page.login("' OR '1'='1", "password")
        error = login_page.get_error_message()
        assert error  # Any error is fine — just shouldn't succeed

    def test_locked_account(self, login_page: LoginPage):
        """BFSI: Locked account should show specific message, not generic error."""
        login_page.login("locked_user@bank.com", "AnyPassword@1")
        error = login_page.get_error_message()
        assert "account" in error.lower() and "locked" in error.lower()

    def test_max_failed_attempts_lockout(self, login_page: LoginPage, page: Page):
        """Security: Account should lock after 3 failed attempts (BFSI requirement)."""
        for attempt in range(3):
            login_page.navigate(BASE_URL)
            login_page.login("target_user@bank.com", f"WrongPass{attempt}")

        error = login_page.get_error_message()
        assert "locked" in error.lower() or "disabled" in error.lower()


@pytest.mark.regression
class TestTwoFactorAuth:

    def test_2fa_prompt_appears(self, login_page: LoginPage, page: Page):
        """After valid credentials, 2FA OTP screen should appear."""
        login_page.login("2fa_user@bank.com", "ValidPass@123")
        expect(page.locator("#otp-input")).to_be_visible(timeout=5_000)

    def test_invalid_otp_rejected(self, login_page: LoginPage, page: Page):
        """Invalid OTP should not grant access."""
        login_page.login("2fa_user@bank.com", "ValidPass@123")
        login_page.submit_otp("000000")
        expect(page.locator(".otp-error")).to_be_visible()

    def test_expired_otp_rejected(self, login_page: LoginPage, page: Page):
        """Expired OTP (>5 min) should be rejected with expiry message."""
        login_page.login("2fa_user@bank.com", "ValidPass@123")
        login_page.submit_otp("123456")  # Assume this is an expired OTP in test env
        error_text = page.locator(".otp-error").inner_text()
        assert "expired" in error_text.lower()


@pytest.mark.visual
def test_login_visual_regression(page: Page, assert_snapshot):
    """Visual regression: Login page should match approved baseline."""
    page.goto(f"{BASE_URL}/auth/login")
    assert_snapshot(page.screenshot(), "login-page-baseline.png")
