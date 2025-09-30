# -*- coding: utf-8 -*-
"""Use Playwright to log in and click the button."""
import traceback
import logging
import argparse
from time import time
import random

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Locator, TimeoutError

from . import last_run_at_absolute_path, login_page
from .browsers import get_browser


# Global variables so someone can monkey patch
# if they want to -- in case this breaks
USERNAME_ID = "id_auth-username"
PASSWORD_ID = "id_auth-password"
LOGIN_BUTTON_ID = "id_next"
RUN_BUTTON_SELECTOR = "input.webapp_extend[type='submit']"
LOGOUT_BUTTON_SELECTOR = "button.logout_link[type='submit']"
EXPIRY_DATE_TAG_SELECTOR = 'p.webapp_expiry > strong'
LOGIN_ERROR_ID = 'id_login_error'

TIMEOUT = 30000  # milliseconds


def close_everything(browser: Browser, context: BrowserContext) -> str:
    """Gracefully close everything."""
    try:
        context.close()
        browser.close()
        return "Closed gracefully."
    except Exception:
        return ''


def navigate_to_page(page: Page, url: str) -> tuple[bool, str]:
    """Navigate to the page and returns a tuple of status and message."""
    try:
        page.goto(url)
    except TimeoutError:
        return False, f"Timed out after {TIMEOUT/1000:g} s."
    except Exception as e:
        return False, e
    else:
        return True, ''


def log_in(page: Page, url: str, credentials: dict) -> tuple[bool, str]:
    """Logs in and returns a tuple of status and message."""
    success, msg = navigate_to_page(page, url)
    if not success:
        return False, f"Unable to load {url}: {msg}"
    if not credentials:
        return False, "Unable to get PythonAnywhere credentials."
    # Enter username and password
    page.type(f"#{USERNAME_ID}", credentials["username"], delay=random.uniform(50, 100))
    page.type(f"#{PASSWORD_ID}", credentials["password"], delay=random.uniform(50, 100))
    # Click 'Log in'
    try:
        with page.expect_navigation():
            page.click(f"#{LOGIN_BUTTON_ID}")
    except TimeoutError:
        return False, f"Timed out logging in after {TIMEOUT/1000:g} s."
    # Check if there is any error message
    err_locator = page.locator(f"#{LOGIN_ERROR_ID}")
    if err_locator.is_visible():
        return False, f"Unable to log in: {err_locator.inner_text()}"
    # Check the logout button
    logout_locator = page.locator(LOGOUT_BUTTON_SELECTOR)  # may find multiple matches
    if logout_locator.count() == 0:
        return False, f"Credentials are correct but couldn't find the '{LOGOUT_BUTTON_SELECTOR}' button."
    return True, "Logged in."


def log_out(page: Page) -> str:
    """Logs out or returns an empty string."""
    try:
        page.click(LOGOUT_BUTTON_SELECTOR)
        return "Logged out."
    except Exception:
        return ''


def get_expiry_date(page: Page, url: str) -> tuple[bool, str, Locator | None]:
    """Navigates to the 'Web' page and finds the button and the expiry date locator."""
    success, msg = navigate_to_page(page, url)
    if not success:
        return success, f"Unable to load {url}: {msg}", None

    date_locator = page.locator(EXPIRY_DATE_TAG_SELECTOR)
    if date_locator.is_visible():
        return True, f"Initial expiry date: {date_locator.inner_text()}", date_locator
    else:
        return False, "Expiry date not found.", None


def extend_expiry_date(page: Page, date_locator: Locator) -> tuple[bool, str, str]:
    """Clicks the 'Run until 3 months from today' button and
    returns a tuple of status, message, and extra information.
    """
    btn_locator = page.locator(RUN_BUTTON_SELECTOR)
    if not (btn_locator.is_visible() and btn_locator.is_enabled()):
        return False, "Button not found or disabled.", ''

    # The page will reload once the button is clicked
    try:
        with page.expect_navigation():
            btn_locator.click()
    except TimeoutError:
        success = False  # It might be fine, just give a warning later
        msg = f"Timed out reloading the page after {TIMEOUT} s."
    else:
        success = True
        msg = "Expiry date extended successfully."
    finally:
        date = date_locator.inner_text()
        return success, msg, f"Current expiry date: {date}"


# Encapsulate main functionality, can import any use in code instead
# of running from cmdline
def run(
    credentials: dict,
    args: argparse.Namespace,
    logger: logging.Logger = logging.getLogger(),
) -> bool:
    with sync_playwright() as p:
        browser = get_browser(p, args, logger)
        if browser is None:
            return False

        context = browser.new_context()  # incognito
        page = context.new_page()
        context.set_default_timeout(TIMEOUT)
        is_logged_in = False

        try:
            if args.test:
                logger.info("*** Test only (no operation) ***")
                return True

            # Login ---------------------------------------------------|
            success, msg = log_in(page, login_page, credentials)
            if success:
                logger.info(msg)
                is_logged_in = True
            else:
                logger.error(msg)
                return False

            # Go to "Web" page ----------------------------------------|
            success, msg, date_locator = get_expiry_date(page, page.url + "/webapps")
            if success:
                logger.info(msg)
            else:
                logger.error(msg)
                return False

            # Click 'Run until 3 months from today' -------------------|
            success, msg, extra_info = extend_expiry_date(page, date_locator)
            if success:
                logger.info(msg)
            elif extra_info:
                logger.warning(msg)
            else:
                logger.error(msg)
                return False
            logger.info(extra_info)

            # Save current time to 'last run time file', so we can check if we need to run this again
            with open(last_run_at_absolute_path, "w") as f:
                f.write(str(time()))

        except Exception:
            traceback.print_exc()
            return False

        else:
            return True

        finally:
            # Log out
            if is_logged_in:
                logger.info(log_out(page))
            # Close
            logger.info(close_everything(browser, context))
