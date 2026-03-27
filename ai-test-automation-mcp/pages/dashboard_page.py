"""
Dashboard Page — Page Object Model
=====================================
Handles all dashboard interactions post-login.
"""

from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class DashboardPage(BasePage):

    # Locators
    WELCOME_MESSAGE   = (By.CSS_SELECTOR, ".welcome-header")
    ACCOUNT_BALANCE   = (By.CSS_SELECTOR, ".account-balance .amount")
    ACCOUNT_NUMBER    = (By.CSS_SELECTOR, ".account-number")
    TRANSACTIONS_TAB  = (By.ID, "tab-transactions")
    TRANSFER_BUTTON   = (By.CSS_SELECTOR, "button.transfer-funds")
    LOGOUT_BUTTON     = (By.CSS_SELECTOR, "button.logout")
    NOTIFICATION_BELL = (By.ID, "notification-bell")
    ACCOUNT_CARDS     = (By.CSS_SELECTOR, ".account-card")

    URL_FRAGMENT = "/dashboard"

    def is_dashboard_loaded(self) -> bool:
        return self.is_visible(self.WELCOME_MESSAGE)

    def get_welcome_message(self) -> str:
        return self.get_text(self.WELCOME_MESSAGE)

    def get_account_balance(self) -> str:
        return self.get_text(self.ACCOUNT_BALANCE)

    def get_account_number(self) -> str:
        return self.get_text(self.ACCOUNT_NUMBER)

    def click_transactions_tab(self):
        self.click(self.TRANSACTIONS_TAB)

    def click_transfer_button(self):
        self.click(self.TRANSFER_BUTTON)

    def logout(self):
        self.click(self.LOGOUT_BUTTON)
        self.wait_for_url("/login")

    def get_account_cards_count(self) -> int:
        cards = self.driver.find_elements(*self.ACCOUNT_CARDS)
        return len(cards)
