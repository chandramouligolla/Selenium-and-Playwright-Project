"""
Base Page — Page Object Model (POM)
=====================================
All page classes inherit from BasePage.
Provides common Selenium WebDriver actions with built-in waits,
logging, and error handling for BFSI-grade stability.
"""

import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all Page Objects."""

    DEFAULT_TIMEOUT = 15

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)
        self.actions = ActionChains(driver)

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self, url: str):
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title

    # ── Element Interactions ──────────────────────────────────────────────────

    def find_element(self, locator, timeout=None):
        t = timeout or self.DEFAULT_TIMEOUT
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            logger.error(f"Element not found: {locator}")
            raise

    def click(self, locator, timeout=None):
        logger.debug(f"Clicking: {locator}")
        element = WebDriverWait(self.driver, timeout or self.DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()

    def type_text(self, locator, text: str, clear_first=True):
        logger.debug(f"Typing '{text}' into: {locator}")
        element = self.find_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def get_text(self, locator) -> str:
        return self.find_element(locator).text.strip()

    def is_visible(self, locator, timeout=5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url(self, url_fragment: str, timeout=None):
        WebDriverWait(self.driver, timeout or self.DEFAULT_TIMEOUT).until(
            EC.url_contains(url_fragment)
        )

    def take_screenshot(self, name: str):
        path = f"reports/screenshots/{name}.png"
        self.driver.save_screenshot(path)
        logger.info(f"Screenshot saved: {path}")
        return path
