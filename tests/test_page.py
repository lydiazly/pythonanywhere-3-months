# -*- coding: utf-8 -*-
# tests/test_page.py
# pytest tests/test_page.py --browser-channel chromium
from playwright.sync_api import Page, expect

from pythonanywhere_3_months.config import LOGIN_PAGE_URL
from pythonanywhere_3_months.selectors import Selectors


def test_page(page: Page):
    """Tests landing page."""
    page.goto(LOGIN_PAGE_URL)
    # Expects login form and button to be visible
    expect(page.locator(Selectors.USERNAME)).to_be_visible()
    expect(page.locator(Selectors.PASSWORD)).to_be_visible()
    expect(page.locator(Selectors.LOGIN_BUTTON)).to_be_visible()
