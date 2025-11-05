# -*- coding: utf-8 -*-
# config.py
"""Configuration and constants."""

from argparse import Namespace
import os
from pathlib import Path
from typing import NamedTuple


LOCAL_DIRECTORY: Path = Path(
    os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")
)

# Credentials
CREDENTIAL_FILE_NAME: str = os.getenv(
    'CREDENTIAL_FILE_NAME', "pythonanywhere_credentials.yaml"
)
CREDENTIAL_ABSOLUTE_PATH: Path = (
    LOCAL_DIRECTORY / CREDENTIAL_FILE_NAME
).resolve()

# File to store the timestamp of last run
LAST_RUN_AT_FILE_NAME: str = os.getenv(
    'LAST_RUN_AT_FILE_NAME', "pythonanywhere_lastrun.txt"
)
LAST_RUN_AT_ABSOLUTE_PATH: Path = (
    LOCAL_DIRECTORY / LAST_RUN_AT_FILE_NAME
).resolve()

# Home page
LOGIN_PAGE_URL: str = os.getenv(
    'LOGIN_PAGE_URL', "https://www.pythonanywhere.com/login/"
)
# The subdirectory of 'Web' tab
TARGET_URL_SUBDIR: str = os.getenv('TARGET_URL_SUBDIR', "webapps")

# Timeout in milliseconds
TIMEOUT = int(os.getenv('TIMEOUT', 30000))

# Available browsers
BROWSER_CHOICES = ['chromium', 'firefox', 'webkit']


class Config(NamedTuple):
    """Application configuration.

    Attributes:
        peek_only (bool): Find the expiry date without clicking the button
        debug (bool): Set the logging level to DEBUG
        test (bool): Exit after opening a page without any further operation
        headed_mode (bool): Headed mode
        browser_name (str): Browser name
        headless_shell (bool): Use a separate chromium headless shell
    """

    peek_only: bool
    debug: bool
    test: bool
    headed_mode: bool
    browser_name: str
    headless_shell: bool


def load_config(args: Namespace) -> Config:
    """Loads configuration from args."""
    return Config(
        peek_only=args.peek,
        debug=args.debug,
        test=args.test,
        headed_mode=args.headed,
        browser_name=args.browser,
        headless_shell=args.shell,
    )
