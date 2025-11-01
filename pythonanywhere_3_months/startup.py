# -*- coding: utf-8 -*-
# startup.py
"""Logger setter and CLI argument parsers."""
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
import logging
from pathlib import Path
import sys
import yaml

from pythonanywhere_3_months.config import BROWSER_CHOICES


# ---------------------------------------------------------------------|
# Logging
class DebugLogFormatter(logging.Formatter):
    """Debug level logging formatter."""

    FMT = "[%(asctime)s %(levelno)s] %(message)s"
    FMT_ERR = (
        "[%(asctime)s %(levelno)s] (%(levelname)s) %(message)s "
        "(%(filename)s:%(lineno)d)"
    )
    FORMATTERS = {
        logging.DEBUG: logging.Formatter(FMT),
        logging.INFO: logging.Formatter(FMT),
        logging.WARNING: logging.Formatter(FMT_ERR),
        logging.ERROR: logging.Formatter(FMT_ERR),
        logging.CRITICAL: logging.Formatter(FMT_ERR),
    }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.FORMATTERS.get(
            record.levelno, logging.Formatter(self.FMT)
        )
        return formatter.format(record)


def setup_logger(name: str = '') -> logging.Logger:
    """Sets and returns a logger."""
    if name:
        # Level: INFO, use a local logger with a name
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        # Suppress urllib3 warnings
        logging.getLogger('urllib3').setLevel(logging.ERROR)
    else:
        # Level: DEBUG, use the root logger
        # Create handler with custom formatter
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(DebugLogFormatter())
        logging.basicConfig(
            level=logging.DEBUG,
            # format="%(asctime)s %(levelno)s - %(message)s",
            handlers=[handler],
        )
        logger = logging.getLogger()
    return logger


# ---------------------------------------------------------------------|
# CLI arguments
def get_args_and_logger() -> tuple[Namespace, logging.Logger]:
    """Gets CLI arguments and sets the logger."""
    parser = ArgumentParser(
        usage="%(prog)s [-h] [options]",
        description="Extends the expiry date of your webapp on PythonAnywhere.",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        '-H',
        '--headed',
        action='store_true',
        help="Run in headed mode (default: headless)",
    )
    parser.add_argument(
        '-b',
        '--browser',
        metavar='str',
        choices=BROWSER_CHOICES,
        default='chromium',
        help="Select a browser from: %(choices)s (default: %(default)s)",
    )
    parser.add_argument(
        '--headless-shell',
        dest='shell',
        action='store_true',
        help=(
            "Use a separate headless shell for chromium headless mode\n"
            "(https://playwright.dev/python/docs/browsers#chromium-headless-shell)"
        ),
    )
    parser.add_argument(
        '--peek',
        action='store_true',
        help=(
            "Find the expiry date and exit without clicking the extend button "
            "(default: false)"
        ),
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help=(
            "Set the logging level to DEBUG "
            "(default to false or from $DEBUG_MODE)"
        ),
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help=(
            "Exit after opening a page without any further operation "
            "(default: false)"
        ),
    )
    args = parser.parse_args()

    logger = setup_logger('' if args.debug else __name__)
    logger.debug(f"Args:\n{vars(args)}")

    return args, logger


def get_credentials(
    credentials_path: Path,
    logger: logging.Logger = logging.getLogger(),
) -> dict[str, str]:
    """Reads PythonAnywhere credentials from a file.

    If the file is empty or not found, prompt the user for input then save them.
    """
    credentials: dict[str, str] = {}
    file_exists: bool = False

    # Read from file
    if credentials_path.is_file():
        logger.debug(f"Credential file: {str(credentials_path)}")
        credentials = yaml.safe_load(
            credentials_path.read_text(encoding="utf-8")
        )
        file_exists = True

    # Or prompt for input
    if not credentials:
        from getpass import getpass

        print("Please enter your PythonAnywhere username and password")
        print(
            "(Your credentials will be saved locally on your device "
            "and are not collected by us)"
        )
        credentials['username'] = input("Username: ").strip()
        credentials['password'] = getpass("Password: ").strip()

    # Check and return
    if (
        credentials
        and isinstance(credentials, dict)
        and all(
            k in credentials and credentials[k]
            for k in ['username', 'password']
        )
    ):
        if not file_exists:
            credentials_path.parent.mkdir(parents=True, exist_ok=True)
            credentials_path.write_text(
                yaml.dump(credentials, indent=2, sort_keys=False),
                encoding="utf-8",
            )
            logger.info(f"Saved credentials: {str(credentials_path)}")
        return credentials
    else:
        raise ValueError("Invalid PythonAnywhere credentials.")
