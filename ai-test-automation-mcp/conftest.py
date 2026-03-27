"""
conftest.py — Shared PyTest Fixtures
Selenium + Playwright + DB connections
Author: Golla Chandramouli | SDET
"""

import pytest
import os
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions


# ─── CONFIG ───────────────────────────────────
BASE_URL = os.getenv("APP_URL", "https://demo.banking-app.com")
API_URL = os.getenv("API_BASE_URL", "https://api.banking-app.com/v1")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


# ─── PLAYWRIGHT FIXTURES ──────────────────────
@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir="reports/videos/" if not HEADLESS else None
    )
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    yield page
    page.close()


# ─── SELENIUM FIXTURES ────────────────────────
@pytest.fixture(scope="session")
def selenium_driver():
    options = ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


# ─── PYTEST HOOKS ─────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: fast smoke test suite")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "performance: performance/load tests")
    config.addinivalue_line("markers", "visual: visual regression tests")
    config.addinivalue_line("markers", "security: security-focused tests")
    config.addinivalue_line("markers", "api: API-only tests")
    config.addinivalue_line("markers", "ui: UI-only tests")
    config.addinivalue_line("markers", "db: DB validation tests")


def pytest_runtest_logreport(report):
    """Capture screenshots on test failure for debugging."""
    if report.when == "call" and report.failed:
        pass  # Hook for screenshot capture — integrate with your page fixture
