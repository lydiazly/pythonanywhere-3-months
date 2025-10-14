# -*- coding: utf-8 -*-
# core.py
"""Main functions to log in and click the button."""
from logging import Logger, getLogger
from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError,
)
import random
from time import time
import traceback

from pythonanywhere_3_months.config import (
    Config,
    LAST_RUN_AT_ABSOLUTE_PATH,
    LOGIN_PAGE_URL,
    TARGET_URL_SUBDIR,
    TIMEOUT,
)
from pythonanywhere_3_months.browsers import get_browser
from pythonanywhere_3_months.selectors import LoginIds, Selectors


TIMEOUT_ERR_TEMPLATE = "Timeout %s after %gs."


def print_error(
    exc: Exception | BaseException, logger: Logger, max_level: int = 5
) -> None:
    """Prints error messages and causes."""
    current_exc = exc
    level = 1
    while current_exc is not None and level <= max_level:
        logger.error(f"{'  └─ ' if level > 1 else ''}{current_exc}")
        if current_exc.__cause__ is not None:
            current_exc = current_exc.__cause__
            level += 1
        elif current_exc.__context__ is not None:
            current_exc = current_exc.__context__
            level += 1
        else:
            return


def close_everything(
    browser: Browser, context: BrowserContext, logger: Logger
) -> None:
    """Gracefully closes everything."""
    context.close()
    browser.close()
    logger.info("Browser closed.")


def navigate_to_page(page: Page, url: str) -> None:
    """Navigates to the page."""
    try:
        page.goto(url)
        page.wait_for_load_state("networkidle")
    except TimeoutError:
        raise TimeoutError(
            TIMEOUT_ERR_TEMPLATE % (f"loading {url}", TIMEOUT / 1000)
        )
    except Exception as e:
        raise RuntimeError(f"Unable to load {url}.") from e


def log_in(
    page: Page, url: str, credentials: dict[str, str], logger: Logger
) -> None:
    """Navigates to the landing page and logs in."""
    navigate_to_page(page, url)

    # Enter username and password
    page.type(
        f"#{LoginIds.USERNAME}",
        credentials["username"],
        delay=random.uniform(50, 100),
    )
    page.type(
        f"#{LoginIds.PASSWORD}",
        credentials["password"],
        delay=random.uniform(50, 100),
    )

    # Click 'Log in'
    try:
        with page.expect_navigation():
            page.click(f"#{LoginIds.LOGIN_BUTTON}")
    except TimeoutError:
        raise TimeoutError(
            TIMEOUT_ERR_TEMPLATE % ("logging in", TIMEOUT / 1000)
        )

    # Check if there is any error messages
    err_locator = page.locator(f"#{LoginIds.LOGIN_ERROR}")
    if err_locator.is_visible():
        raise RuntimeError(f"Unable to log in: {err_locator.inner_text()}")

    # Check the logout button
    logout_locator = page.locator(
        Selectors.LOGOUT_BUTTON
    )  # may find multiple matches
    if logout_locator.count() == 0:
        raise RuntimeError(
            "Maybe logged in but couldn't find the logout button."
        )

    logger.info("Logged in.")


def log_out(page: Page, is_logged_in: bool, logger: Logger) -> None:
    """Logs out."""
    if is_logged_in:
        try:
            page.click(Selectors.LOGOUT_BUTTON)
        except Exception as e:
            logger.error(f"Error logging out:\n{type(e).__name__}: {e}")
        else:
            logger.info("Logged out.")


def extend_expiry_date(
    page: Page, url: str, logger: Logger, peek_only: bool = False
) -> None:
    """Navigates to the page, finds the the expiry date, then clicks the
    `Run until 3 months from today` button.
    """
    navigate_to_page(page, url)

    date_locator = page.locator(Selectors.EXPIRY_DATE_TAG)
    try:
        date_locator.wait_for(state="visible", timeout=TIMEOUT)
    except TimeoutError:
        raise TimeoutError(
            TIMEOUT_ERR_TEMPLATE % ('looking for expiry date', TIMEOUT / 1000)
        )

    if peek_only:
        logger.info("*** Peek only (no clicking) ***")
        logger.info(f"Current expiry date: {date_locator.inner_text()}")
        return
    else:
        logger.info(f"Initial expiry date: {date_locator.inner_text()}")

    btn_locator = page.locator(Selectors.RUN_BUTTON)
    if not (btn_locator.is_visible() and btn_locator.is_enabled()):
        raise RuntimeError("Extend button not found or disabled.")

    # The page will reload once the button is clicked
    try:
        with page.expect_navigation():
            btn_locator.click()
    except TimeoutError:
        raise TimeoutError(
            TIMEOUT_ERR_TEMPLATE % ("reloading the page", TIMEOUT / 1000)
        )
    else:
        logger.info("Expiry date extended successfully.")
    finally:
        date = date_locator.inner_text()
        logger.info(f"Current expiry date: {date}")


def run(
    credentials: dict[str, str],
    config: Config,
    logger: Logger = getLogger(),
) -> None:
    """Main function to run the application."""
    with sync_playwright() as p:
        browser = get_browser(p, config, logger)
        if browser is None:
            logger.error(
                f"{config.browser_name} not launched: unknown error occurred."
            )
            raise RuntimeError

        context = browser.new_context()  # incognito
        page = context.new_page()
        context.set_default_timeout(TIMEOUT)
        is_logged_in = False

        # Do everything in the block for cleanup on exit
        try:
            if config.test:
                # Test and exit
                logger.info("*** Test only (no operation) ***")
                return

            # Go to the landing page and log in -----------------------|
            log_in(page, LOGIN_PAGE_URL, credentials, logger)
            is_logged_in = True

            # Go from 'Dashboard' to 'Web' tab ------------------------|
            # Click 'Run until 3 months from today'
            extend_expiry_date(
                page,
                f"{page.url.rstrip('/')}/{TARGET_URL_SUBDIR}",
                logger,
                config.peek_only,
            )

            # Save current time to a file
            with open(LAST_RUN_AT_ABSOLUTE_PATH, "w") as f:
                f.write(str(time()))

        except TimeoutError as e:
            print_error(e, logger, max_level=2)
            raise

        # Chained exceptions are handled here
        except RuntimeError as e:
            print_error(e, logger)
            raise

        # Other unexpected exceptions
        except Exception as e:
            if config.debug:
                traceback.print_exc()
            else:
                print_error(e, logger)
            raise

        else:
            logger.info("Done!")

        # Cleanup
        finally:
            # Log out
            log_out(page, is_logged_in, logger)
            # Close
            close_everything(browser, context, logger)
