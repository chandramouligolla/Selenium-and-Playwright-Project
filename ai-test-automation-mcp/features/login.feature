# ─────────────────────────────────────────────────────────────────────────────
# Feature: Secure Banking Login with 2FA
# Framework: Behave BDD (Python) | Gherkin
# Domain: BFSI | Lloyds Banking Group
# Author: Golla Chandramouli | SDET
# ─────────────────────────────────────────────────────────────────────────────

Feature: Secure Banking Login with Two-Factor Authentication
  As a registered banking customer
  I want to log in to my account securely
  So that I can manage my finances safely

  Background:
    Given the banking application is available
    And I am on the login page

  # ─── SMOKE TESTS ─────────────────────────────────────────
  @smoke @login
  Scenario: Successful login with valid credentials and OTP
    Given I have a registered account with username "customer@bank.com"
    When I enter my valid password
    And I submit the login form
    Then I should be prompted for a one-time passcode
    When I enter the valid OTP from my authenticator app
    Then I should be redirected to my account dashboard
    And my account summary should be displayed

  @smoke @login
  Scenario: Login page displays all required elements
    Then the username field should be visible
    And the password field should be visible
    And the login button should be enabled
    And the "Forgot Password" link should be present

  # ─── REGRESSION — NEGATIVE TESTS ─────────────────────────
  @regression @negative
  Scenario: Login fails with invalid password
    Given I have a registered account with username "customer@bank.com"
    When I enter an incorrect password "WrongPass@999"
    And I submit the login form
    Then I should see the error message "Invalid credentials. Please try again."
    And I should remain on the login page
    And the failed attempt should be recorded in the audit log

  @regression @negative
  Scenario: Login fails with unregistered email
    When I enter username "notregistered@bank.com"
    And I enter any password "AnyPass@123"
    And I submit the login form
    Then I should see the error message "Invalid credentials. Please try again."

  @regression @negative
  Scenario Outline: Login form validation for empty fields
    When I enter username "<username>"
    And I enter password "<password>"
    And I submit the login form
    Then the form should show validation error "<error_field>"

    Examples:
      | username              | password       | error_field |
      |                       | SomePass@1     | username    |
      | customer@bank.com     |                | password    |
      |                       |                | username    |

  # ─── SECURITY TESTS ──────────────────────────────────────
  @regression @security
  Scenario: Account locks after 3 consecutive failed login attempts
    Given I have a registered account with username "customer@bank.com"
    When I fail to login "3" times with wrong passwords
    Then my account should be temporarily locked
    And I should see the message "Account locked. Please contact support."
    And a security alert email should be sent to my registered address

  @regression @security
  Scenario: SQL injection attempt is safely rejected
    When I enter username "' OR '1'='1'; --"
    And I enter password "' OR '1'='1'; --"
    And I submit the login form
    Then I should see an error message
    And no database query should be executed with raw input
    And the attempt should be flagged in the security audit log

  @regression @security
  Scenario: Session expires after inactivity timeout
    Given I am logged in to my account
    When I remain inactive for "15" minutes
    Then my session should automatically expire
    And I should be redirected to the login page
    And I should see the message "Your session has expired for security reasons."

  # ─── 2FA TESTS ───────────────────────────────────────────
  @regression @2fa
  Scenario: Invalid OTP is rejected
    Given I have entered valid credentials for "2fa_user@bank.com"
    And I am on the OTP verification screen
    When I enter an invalid OTP "000000"
    And I submit the OTP
    Then I should see the message "Invalid code. Please try again."
    And I should remain on the OTP screen

  @regression @2fa
  Scenario: Expired OTP is rejected
    Given I have entered valid credentials for "2fa_user@bank.com"
    And I am on the OTP verification screen
    When I enter an OTP that was generated more than 5 minutes ago
    Then I should see the message "Code has expired. Please request a new one."
