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
from types import TracebackType
from typing import Self, Literal

from pythonanywhere_3_months.config import (
    Config,
    LAST_RUN_AT_ABSOLUTE_PATH,
    LOGIN_PAGE_URL,
    TARGET_URL_SUBDIR,
    TIMEOUT,
)
from pythonanywhere_3_months.browsers import get_browser
from pythonanywhere_3_months.selectors import Selectors


TIMEOUT_ERR_TEMPLATE = "Timeout %s after %gs."
INITIAL_DATE_TEMPLATE = "Initial expiry date: %s"
CURRENT_DATE_TEMPLATE = "Current expiry date: %s"
EXTENDED_MSG = "Expiry date extended successfully."
TEST_MSG = "*** Test only (no operation) ***"
PEEK_MSG = "*** Peek only (no clicking) ***"
BROWSER_CLOSED_MSG = "Browser closed."


class PageManager:
    LOGGED_IN_MSG = "Logged in."
    LOGGED_OUT_MSG = "Logged out."

    def __init__(
        self,
        browser: Browser,
        credentials: dict[str, str],
        home_url: str,
        url_sub_dir: str,
        config: Config,
        logger: Logger = getLogger(),
    ) -> None:
        self.browser: Browser = browser
        self.credentials: dict[str, str] = credentials
        self.home_url: str = home_url
        self.url_sub_dir: str = url_sub_dir
        self.sub_url: str = ''
        self.config: Config = config
        self.logger: Logger = logger
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.is_logged_in: bool = False

    def __enter__(self) -> Self:
        self.page = self.open_page()
        if self.context:
            self.context.set_default_timeout(TIMEOUT)
        if not self.config.test:
            self.log_in()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        if self.is_logged_in:
            self.log_out()
        self.close()
        return False

    def open_page(self) -> Page:
        if not self.context:
            self.context = self.browser.new_context()  # incognito
        return self.context.new_page()

    def close(self) -> None:
        """Gracefully closes context."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass

    def print_error(
        self, exc: Exception | BaseException, max_level: int = 5
    ) -> None:
        """Prints error messages and causes."""
        current_exc = exc
        level = 1
        while current_exc is not None and level <= max_level:
            self.logger.error(f"{'  └─ ' if level > 1 else ''}{current_exc}")
            if current_exc.__cause__ is not None:
                current_exc = current_exc.__cause__
                level += 1
            elif current_exc.__context__ is not None:
                current_exc = current_exc.__context__
                level += 1
            else:
                return

    @staticmethod
    def goto_page(page: Page, url: str) -> None:
        """Navigates to the page."""
        try:
            page.goto(url, wait_until='domcontentloaded')
        except TimeoutError:
            raise TimeoutError(
                TIMEOUT_ERR_TEMPLATE % (f"loading {url}", TIMEOUT / 1000)
            )
        except Exception as e:
            raise RuntimeError(f"Unable to load {url}.") from e

    def log_in(self) -> None:
        """Navigates to the landing page and logs in."""
        if not self.home_url:
            return

        if not self.page:
            self.page = self.open_page()

        self.goto_page(self.page, self.home_url)

        # Enter username and password
        self.page.type(
            Selectors.USERNAME,
            self.credentials["username"],
            delay=random.uniform(50, 100),
        )
        self.page.type(
            Selectors.PASSWORD,
            self.credentials["password"],
            delay=random.uniform(50, 100),
        )

        # Click 'Log in'
        try:
            with self.page.expect_navigation():
                self.page.click(Selectors.LOGIN_BUTTON)
        except TimeoutError:
            raise TimeoutError(
                TIMEOUT_ERR_TEMPLATE % ("logging in", TIMEOUT / 1000)
            )

        # Check if there is any error messages
        err_locator = self.page.locator(Selectors.LOGIN_ERROR).describe(
            "Login error message"
        )
        if err_locator.is_visible():
            raise RuntimeError(f"Unable to log in: {err_locator.inner_text()}")

        # Check the logout button
        logout_locator = self.page.locator(Selectors.LOGOUT_BUTTON).describe(
            "Logout button"
        )  # may find multiple matches
        if logout_locator.count() == 0:
            raise RuntimeError(
                "Maybe logged in but couldn't find the logout button."
            )

        self.sub_url = f"{self.page.url.rstrip('/')}/{self.url_sub_dir}"
        self.is_logged_in = True
        self.logger.info(self.LOGGED_IN_MSG)

    def log_out(self) -> None:
        """Logs out."""
        if not self.page:
            return

        try:
            self.page.click(Selectors.LOGOUT_BUTTON)
        except Exception as e:
            self.logger.error(f"Error logging out:\n{type(e).__name__}: {e}")
        else:
            self.is_logged_in = False
            self.logger.info(self.LOGGED_OUT_MSG)

    def extend_expiry_date(self) -> None:
        """Navigates to the page, finds the the expiry date, then clicks the
        `Run until 3 months from today` button.
        """
        if not self.page:
            raise RuntimeError("Page closed.")

        if not self.sub_url:
            return

        self.goto_page(self.page, self.sub_url)

        date_locator = self.page.locator(Selectors.EXPIRY_DATE_TAG).describe(
            "Date"
        )
        try:
            date_locator.wait_for(state="visible", timeout=TIMEOUT)
        except TimeoutError:
            raise TimeoutError(
                TIMEOUT_ERR_TEMPLATE
                % ('looking for expiry date', TIMEOUT / 1000)
            )

        if self.config.peek_only:
            self.logger.info(PEEK_MSG)
            self.logger.info(CURRENT_DATE_TEMPLATE % date_locator.inner_text())
            return
        else:
            self.logger.info(INITIAL_DATE_TEMPLATE % date_locator.inner_text())

        btn_locator = self.page.locator(Selectors.EXTEND_BUTTON)
        if not (btn_locator.is_visible() and btn_locator.is_enabled()):
            raise RuntimeError("Extend button not found or disabled.")

        # The page will reload once the button is clicked
        try:
            with self.page.expect_navigation():
                btn_locator.click()
        except TimeoutError:
            raise TimeoutError(
                TIMEOUT_ERR_TEMPLATE % ("reloading the page", TIMEOUT / 1000)
            )
        else:
            self.logger.info(EXTENDED_MSG)
        finally:
            date = date_locator.inner_text()
            self.logger.info(CURRENT_DATE_TEMPLATE % date)


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

        try:
            # Open page and log in
            with PageManager(
                browser,
                credentials,
                LOGIN_PAGE_URL,
                TARGET_URL_SUBDIR,
                config,
                logger,
            ) as pm:
                if config.test:
                    logger.info(TEST_MSG)
                    return

                # Go from 'Dashboard' to 'Web' tab --------------------|
                # Click 'Run until 3 months from today'
                pm.extend_expiry_date()

                # Save current time to a file -------------------------|
                with open(LAST_RUN_AT_ABSOLUTE_PATH, "w") as f:
                    f.write(str(time()))

        except TimeoutError as e:
            pm.print_error(e, max_level=2)
            raise

        # Chained exceptions are handled here
        except RuntimeError as e:
            pm.print_error(e)
            raise

        # Other unexpected exceptions
        except Exception as e:
            if config.debug:
                traceback.print_exc()
            else:
                pm.print_error(e)
            raise

        else:
            logger.info("Done!")

        # Cleanup
        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass
            finally:
                logger.info(BROWSER_CLOSED_MSG)
