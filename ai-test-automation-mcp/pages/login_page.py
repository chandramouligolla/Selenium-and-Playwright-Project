"""
Login Page — Page Object Model
================================
Handles all login page interactions for Lloyds Banking Group portal.
"""

from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):

    # Locators
    USERNAME_INPUT   = (By.ID, "username")
    PASSWORD_INPUT   = (By.ID, "password")
    LOGIN_BUTTON     = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE    = (By.CSS_SELECTOR, ".error-message")
    REMEMBER_ME      = (By.ID, "rememberMe")
    FORGOT_PASSWORD  = (By.LINK_TEXT, "Forgot Password?")

    URL = "/login"

    def open_login_page(self, base_url: str):
        self.open(f"{base_url}{self.URL}")

    def enter_username(self, username: str):
        self.type_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str):
        self.type_text(self.PASSWORD_INPUT, password)

    def click_login(self):
        self.click(self.LOGIN_BUTTON)

    def login(self, username: str, password: str):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_displayed(self) -> bool:
        return self.is_visible(self.ERROR_MESSAGE)

    def is_login_page(self) -> bool:
        return self.URL in self.get_current_url()
