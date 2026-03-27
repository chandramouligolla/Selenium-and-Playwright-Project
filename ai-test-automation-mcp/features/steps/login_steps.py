"""
BDD Step Definitions — Banking Login with 2FA
Framework: Behave (Python) | Playwright
Author: Golla Chandramouli | SDET
"""

from behave import given, when, then
from playwright.sync_api import sync_playwright, expect


BASE_URL = "https://demo.banking-app.com"


# ─── BACKGROUND ───────────────────────────────
@given("the banking application is available")
def step_app_available(context):
    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=True)
    context.page = context.browser.new_page()
    response = context.page.goto(BASE_URL)
    assert response.status < 500, f"App unavailable. Status: {response.status}"


@given("I am on the login page")
def step_on_login_page(context):
    context.page.goto(f"{BASE_URL}/auth/login")
    expect(context.page.locator("#username")).to_be_visible()


# ─── GIVEN ────────────────────────────────────
@given('I have a registered account with username "{username}"')
def step_registered_user(context, username):
    context.username = username


@given('I have entered valid credentials for "{username}"')
def step_entered_valid_creds(context, username):
    context.page.locator("#username").fill(username)
    context.page.locator("#password").fill("ValidTestPass@1")
    context.page.locator("[data-testid='login-btn']").click()
    expect(context.page.locator("#otp-input")).to_be_visible(timeout=5_000)


@given("I am on the OTP verification screen")
def step_on_otp_screen(context):
    expect(context.page.locator("#otp-input")).to_be_visible()


@given("I am logged in to my account")
def step_logged_in(context):
    context.page.goto(f"{BASE_URL}/auth/login")
    context.page.locator("#username").fill("session_user@bank.com")
    context.page.locator("#password").fill("ValidPass@123")
    context.page.locator("[data-testid='login-btn']").click()
    context.page.locator("#otp-input").fill("123456")
    context.page.locator("[data-testid='verify-otp-btn']").click()
    expect(context.page).to_have_url(f"{BASE_URL}/dashboard", timeout=10_000)


# ─── WHEN ─────────────────────────────────────
@when("I enter my valid password")
def step_enter_valid_password(context):
    context.page.locator("#username").fill(context.username)
    context.page.locator("#password").fill("ValidTestPass@1")


@when('I enter an incorrect password "{password}"')
def step_enter_wrong_password(context, password):
    context.page.locator("#username").fill(context.username)
    context.page.locator("#password").fill(password)


@when('I enter username "{username}"')
def step_enter_username(context, username):
    context.page.locator("#username").fill(username)


@when('I enter any password "{password}"')
def step_enter_any_password(context, password):
    context.page.locator("#password").fill(password)


@when('I enter password "{password}"')
def step_enter_password(context, password):
    context.page.locator("#password").fill(password)


@when("I submit the login form")
def step_submit_login(context):
    context.page.locator("[data-testid='login-btn']").click()


@when("I submit the OTP")
def step_submit_otp(context):
    context.page.locator("[data-testid='verify-otp-btn']").click()


@when("the valid OTP from my authenticator app")
def step_enter_valid_otp(context):
    # In real tests: fetch from TOTP generator or test API
    context.page.locator("#otp-input").fill("123456")
    context.page.locator("[data-testid='verify-otp-btn']").click()


@when('I enter an invalid OTP "{otp}"')
def step_enter_invalid_otp(context, otp):
    context.page.locator("#otp-input").fill(otp)


@when("I enter an OTP that was generated more than 5 minutes ago")
def step_enter_expired_otp(context):
    context.page.locator("#otp-input").fill("999999")  # Test env: pre-seeded as expired


@when('I fail to login "{count}" times with wrong passwords')
def step_fail_login_multiple(context, count):
    for i in range(int(count)):
        context.page.goto(f"{BASE_URL}/auth/login")
        context.page.locator("#username").fill(context.username)
        context.page.locator("#password").fill(f"WrongPass{i}!")
        context.page.locator("[data-testid='login-btn']").click()


@when('I remain inactive for "{minutes}" minutes')
def step_remain_inactive(context, minutes):
    import time
    # In real tests: manipulate server-side session expiry or use test API
    context.page.evaluate(f"document.cookie = 'session_age={int(minutes)*60+10}; path=/'")
    context.page.reload()


# ─── THEN ─────────────────────────────────────
@then("I should be prompted for a one-time passcode")
def step_prompted_for_otp(context):
    expect(context.page.locator("#otp-input")).to_be_visible(timeout=5_000)


@then("I should be redirected to my account dashboard")
def step_redirected_to_dashboard(context):
    expect(context.page).to_have_url(f"{BASE_URL}/dashboard", timeout=10_000)


@then("my account summary should be displayed")
def step_account_summary_visible(context):
    expect(context.page.locator("[data-testid='account-balance']")).to_be_visible()


@then('I should see the error message "{message}"')
def step_see_error_message(context, message):
    error_locator = context.page.locator(".error-banner, .alert-error, [role='alert']")
    expect(error_locator).to_be_visible(timeout=5_000)
    assert message in error_locator.inner_text(), \
        f"Expected: '{message}' | Got: '{error_locator.inner_text()}'"


@then("I should remain on the login page")
def step_remain_on_login(context):
    expect(context.page).to_have_url(f"{BASE_URL}/auth/login")


@then("my account should be temporarily locked")
def step_account_locked(context):
    error = context.page.locator(".error-banner").inner_text()
    assert "locked" in error.lower()


@then("a security alert email should be sent to my registered address")
def step_security_email_sent(context):
    # Verify via test email API (e.g., Mailhog, Mailosaur)
    # In real tests: call email testing service API
    pass  # Placeholder — integrate with Mailosaur in full setup


@then("no database query should be executed with raw input")
def step_no_sql_injection(context):
    # Verify via API audit log endpoint
    pass  # Placeholder — verify via security audit API


@then("the attempt should be flagged in the security audit log")
def step_flagged_in_audit(context):
    pass  # Verify via audit log API


@then("my session should automatically expire")
def step_session_expired(context):
    expect(context.page).to_have_url(f"{BASE_URL}/auth/login", timeout=5_000)


@then('I should see the message "{message}"')
def step_see_message(context, message):
    page_text = context.page.inner_text("body")
    assert message in page_text, f"Message not found: '{message}'"


@then('the form should show validation error "{error_field}"')
def step_form_validation_error(context, error_field):
    field = context.page.locator(f"[data-field='{error_field}'] .field-error")
    expect(field).to_be_visible()


@then("I should remain on the OTP screen")
def step_remain_on_otp(context):
    expect(context.page.locator("#otp-input")).to_be_visible()


@then("the failed attempt should be recorded in the audit log")
def step_audit_log_entry(context):
    pass  # In full setup: verify via audit log API call


# ─── CLEANUP ──────────────────────────────────
def after_scenario(context, scenario):
    """Clean up browser resources after each scenario."""
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "playwright"):
        context.playwright.stop()
