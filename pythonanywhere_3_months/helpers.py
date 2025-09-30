# -*- coding: utf-8 -*-
import argparse
import logging
import sys
from pathlib import Path
import yaml

from . import browser_choices


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
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelno)s - %(message)s")
        logger = logging.getLogger()
    return logger


def get_options() -> tuple[argparse.Namespace, logging.Logger]:
    """Gets options from user and sets the logger."""
    parser = argparse.ArgumentParser(
        description="Clicks the 'Run until 3 months from today' on PythonAnywhere."
    )
    parser.add_argument(
        "-H", "--headed",
        action="store_true",
        help="run in headed mode (default: headless)"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="print debug logs"
    )
    parser.add_argument(
        "-b", "--browser",
        metavar="str",
        choices=browser_choices,
        default="chromium",
        help="specify a browser. Choices: %(choices)s (default: %(default)s)"
    )
    parser.add_argument(
        "--headless-shell",
        dest="shell",
        action="store_true",
        help="use a separate headless shell for chromium headless mode"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="test the browser without any page operation"
    )
    args = parser.parse_args()
    logger = setup_logger('' if args.debug else __name__)
    return args, logger


def get_credentials(filepath: str, logger: logging.Logger = logging.getLogger()) -> dict:
    """Reads PythonAnywhere credentials from a file.
    If the file is empty or not found, prompt the user for input then save them.
    """
    absolute_path = (Path.home() / filepath).resolve()
    credentials = {}
    # Read from file
    if absolute_path.is_file():
        logger.debug(f"Credential file: {absolute_path.as_posix()}")
        credentials = yaml.safe_load(absolute_path.read_text(encoding="utf-8"))
    # Or prompt for input
    if not credentials:
        from getpass import getpass
        print("Please enter your username and password.")
        credentials["username"] = input("Username: ")
        credentials["password"] = getpass("Password: ")
        absolute_path.write_text(yaml.dump(credentials, indent=2, sort_keys=False), encoding="utf-8")
        logger.debug("Saved credentials: {}".format(absolute_path))
    # Check and return
    if (
        credentials
        and isinstance(credentials, dict)
        and all(k in credentials and credentials[k] for k in ["username", "password"])
    ):
        return credentials
    else:
        return {}
