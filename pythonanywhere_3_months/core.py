#!/usr/local/env python3
"""Use Playwright to log in and click the button."""
import os
import sys
import traceback
import logging
import argparse
from time import time
from pathlib import Path
import random

import yaml
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Locator, TimeoutError

from . import (
    last_run_at_absolute_path,
    login_page,
)


# Global variables so someone can monkey patch
# if they want to -- in case this breaks
USERNAME_ID = "id_auth-username"
PASSWORD_ID = "id_auth-password"
LOGIN_BUTTON_ID = "id_next"
RUN_BUTTON_SELECTOR = "input.webapp_extend[type='submit']"
LOGOUT_BUTTON_SELECTOR = "button.logout_link[type='submit']"
EXPIRY_DATE_TAG_SELECTOR = 'p.webapp_expiry > strong'
LOGIN_ERROR_ID = 'id_login_error'

TIMEOUT = 10000  # milliseconds


def setup_logger(name: str = '') -> logging.Logger:
    """Sets and returns the logger."""
    if name:
        # Level=INFO, use a local logger with a name
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        # Suppress urllib3 warnings
        logging.getLogger("urllib3").setLevel(logging.ERROR)
    else:
        # Level=DEBUG, use the root logger
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s %(levelno)s - %(message)s"
        )
        logger = logging.getLogger()
    return logger


def close_everything(browser: Browser, context: BrowserContext) -> None:
    """Gracefully close everything."""
    context.close()
    browser.close()


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


def log_in(page: Page, url: str, username: str, password: str) -> tuple[bool, str]:
    """Logs in and returns a tuple of status and message."""
    success, msg = navigate_to_page(page, url)
    if not success:
        return success, f"Unable to load {url}: {msg}"
    # Enter username and password
    page.type(f"#{USERNAME_ID}", username, delay=random.uniform(50, 100))
    page.type(f"#{PASSWORD_ID}", password, delay=random.uniform(50, 100))
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
        return False, f"Your credentials are correct but can't find the '{LOGOUT_BUTTON_SELECTOR}' button."
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
        return False, "'Button not found or disabled.", ''

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


def get_options() -> tuple[bool, logging.Logger]:
    """Gets options from user and sets the logger."""
    parser = argparse.ArgumentParser(
        description="Clicks the 'Run until 3 months from today' on PythonAnywhere."
    )
    parser.add_argument(
        "-H", "--hidden", help="Hide the browser.", action="store_true"
    )
    parser.add_argument(
        "-d", "--debug", help="Prints debug logs.", action="store_true"
    )
    args = parser.parse_args()
    logger = setup_logger('' if args.debug else __name__)
    return args.hidden, logger


def get_credentials(filepath: str) -> tuple[str, str]:
    """Gets pythonanywhere credentials from the file.
    If the file does not exist, prompt the user for input and save to this path.
    """
    absolute_path = os.path.abspath(os.path.join(Path.home(), filepath))
    if os.path.exists(absolute_path):
        logging.debug("Credential file location: {}".format(absolute_path))
        with open(absolute_path, "r") as cred:
            creds = yaml.load(cred, Loader=yaml.FullLoader)
    else:
        # Prompt the user
        from getpass import getpass
        print("Please enter your username and password.")
        username = input("Username: ")
        password = getpass("Password: ")
        with open(absolute_path, "w") as cred:
            yaml.dump({"username": username, "password": password}, cred)
        logging.debug("Saved credential: {}".format(absolute_path))
        return username, password
    return creds["username"], creds["password"]


# Encapsulate main functionality, can import any use in code instead
# of running from cmdline
def run(
    username: str, password: str, use_hidden: bool = False,
    logger: logging.Logger = logging.getLogger(),
) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=use_hidden)
        context = browser.new_context()  # incognito
        page = context.new_page()
        context.set_default_timeout(TIMEOUT)
        try:
            # Login ---------------------------------------------------|
            success, msg = log_in(page, login_page, username, password)
            if success:
                logger.info(msg)
            else:
                logger.error(msg)
                close_everything(browser, context)
                return

            # Go to "Web" page ----------------------------------------|
            success, msg, date_locator = get_expiry_date(page, page.url + "/webapps")
            if success:
                logger.info(msg)
            else:
                logger.error(msg)
                logger.info(log_out(page))
                close_everything(browser, context)
                return

            # Click 'Run until 3 months from today' -------------------|
            success, msg, extra_info = extend_expiry_date(page, date_locator)
            if success:
                logger.info(msg)
            elif extra_info:
                logger.warning(msg)
            else:
                logger.error(msg)
                logger.info(log_out(page))
                close_everything(browser, context)
                return
            logger.info(extra_info)

            # Save current time to 'last run time file', so we can check if we need to run this again
            with open(last_run_at_absolute_path, "w") as f:
                f.write(str(time()))

            # Log out -------------------------------------------------|
            logger.info(log_out(page))

            print("Done!", file=sys.stderr)
        except Exception:
            traceback.print_exc()
        finally:
            close_everything(browser, context)
