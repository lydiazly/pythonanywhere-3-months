#!/usr/local/env python3

import os
import sys
import traceback
import logging
import argparse
from time import time, sleep
from pathlib import Path
import random

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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

TIMEOUT = 10  # seconds


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


def create_webdriver(
    chromedriver_path: str = '', hide: bool = False
) -> webdriver.Chrome:
    """Creates a webdriver, hides if requested."""
    options = webdriver.ChromeOptions()
    if hide:
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("window-size=1920x1080")
        logging.debug("Creating hidden chrome browser")
    service: webdriver.ChromeService | None
    if chromedriver_path:
        service = webdriver.ChromeService(chromedriver_path)
        logging.debug("Using custom chromedriver path: {}".format(chromedriver_path))
    return webdriver.Chrome(options=options, service=service)  # type: ignore


def log_in(driver: webdriver.Chrome, url: str, username: str, password: str) -> tuple[bool, str]:
    """Logs in and returns a tuple of status and message."""
    driver.get(url)
    try:
        email_input = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.ID, USERNAME_ID))
        )
    except TimeoutException:
        return False, f"Unable to load {url}. Timed out after {TIMEOUT} s."
    # Enter username and password then click 'Log in'
    try:
        password_input = driver.find_element(By.ID, PASSWORD_ID)
        email_input.send_keys(username)
        sleep(random.uniform(0.1, 0.3) * len(username))
        password_input.send_keys(password)
        sleep(random.uniform(0.1, 0.3) * len(password))
        driver.find_element(By.ID, LOGIN_BUTTON_ID).click()
    except Exception as e:
        return False, f"Unable to log in: {e}"
    # Wait for the content to load
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGOUT_BUTTON_SELECTOR))
        )
    except TimeoutException:
        return False, f"Timed out logging in after {TIMEOUT} s."
    return True, "Logged in."


def log_out(driver: webdriver.Chrome) -> str:
    """Logs out or returns an empty string."""
    try:
        driver.find_element(By.CSS_SELECTOR, LOGOUT_BUTTON_SELECTOR).click()
        return "Logged out."
    except Exception:
        return ''


def get_expiry_date(driver: webdriver.Chrome, url: str) -> tuple[bool, str, WebElement | None]:
    """Navigates to the 'Web' page and finds the expiry date."""
    driver.get(url)
    try:
        # The 'Run until 3 months from today' button must be there
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, RUN_BUTTON_SELECTOR))
        )
    except TimeoutException:
        return False, f"'Button not found. Timed out after {TIMEOUT} s.", None
    else:
        element = driver.find_element(By.CSS_SELECTOR, EXPIRY_DATE_TAG_SELECTOR)
        date = element.text
        return True, f"Initial expiry date: {date}", element


def extend_expiry_date(driver: webdriver.Chrome, element: WebElement) -> tuple[bool, list[str]]:
    """Clicks the 'Run until 3 months from today' button."""
    driver.find_element(By.CSS_SELECTOR, RUN_BUTTON_SELECTOR).click()
    try:
        # The page will reload once the button is clicked
        WebDriverWait(driver, TIMEOUT).until(EC.staleness_of(element))
    except TimeoutException:
        date = element.text
        success = False  # It might be fine, just give a warning later
        msg = f"Timed out reloading the page after {TIMEOUT} s."
    else:
        date = driver.find_element(By.CSS_SELECTOR, EXPIRY_DATE_TAG_SELECTOR).text
        success = True
        msg = "Expiry date extended successfully."
    finally:
        return success, [msg, f"Current expiry date: {date}"]


def get_options() -> tuple[bool, str, logging.Logger]:
    """Gets options from user."""
    parser = argparse.ArgumentParser(
        description="Clicks the 'Run until 3 months from today' on PythonAnywhere."
    )
    parser.add_argument(
        "-H", "--hidden", help="Hide the ChromeDriver.", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--chromedriver-path",
        help="Provides the location of ChromeDriver. Should probably be the full path.",
        default=None,
    )
    parser.add_argument("-d", "--debug", help="Prints debug logs.", action="store_true")
    args = parser.parse_args()
    logger = setup_logger('' if args.debug else __name__)
    logger.debug("Custom chromedriver path: {}".format(args.chromedriver_path))
    return args.hidden, args.chromedriver_path, logger


def get_credentials(filepath: str) -> tuple[str, str]:
    """Gets pythonanywhere credentials from the dotfile."""
    absolute_path = os.path.abspath(os.path.join(Path.home(), filepath))
    if os.path.exists(absolute_path):
        logging.debug("Credential file location: {}".format(absolute_path))
        with open(absolute_path, "r") as cred:
            creds = yaml.load(cred, Loader=yaml.FullLoader)
    else:
        # Prompt the user for input and save the credential to the file
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
    username: str, password: str, chromedriver_path: str, use_hidden: bool = False,
    logger: logging.Logger = logging.getLogger(),
) -> None:
    driver: webdriver.Chrome | None = None
    try:
        driver = create_webdriver(chromedriver_path, use_hidden)

        # Login -------------------------------------------------------|
        success, msg = log_in(driver, login_page, username, password)
        if success:
            logger.info(msg)
        else:
            logger.error(msg)
            driver.quit()
            return

        # Go to "Web" page --------------------------------------------|
        success, msg, expiry_date_element = get_expiry_date(driver, driver.current_url + "/webapps")
        if success:
            logger.info(msg)
        else:
            logger.error(msg)
            logger.info(log_out(driver))
            driver.quit()
            return

        # Click 'Run until 3 months from today' -----------------------|
        success, msg_list = extend_expiry_date(driver, expiry_date_element)
        if success:
            logger.info(msg_list[0])
        else:
            logger.warning(msg_list[0])
        logger.info(msg_list[1])

        # Save current time to 'last run time file', so we can check if we need to run this again
        with open(last_run_at_absolute_path, "w") as f:
            f.write(str(time()))

        # Log out -----------------------------------------------------|
        logger.info(log_out(driver))

        print("Done!", file=sys.stderr)
    except Exception:
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
