#!/usr/local/env python3
import logging
import os
import subprocess
import sys
from playwright.sync_api import sync_playwright


def check_and_install_chromium(logger: logging.Logger = logging.getLogger()) -> bool:
    """Checks and installs Chromium."""
    env = os.environ.copy()  # including PLAYWRIGHT_BROWSERS_PATH
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, channel="chromium")
            browser.close()
            return True
    except Exception:
        logger.info("Installing Chromium...")
        # Install
        try:
            subprocess.run(
                [sys.executable, "-m",
                 "playwright", "install", "--with-deps", "--no-shell", "chromium"],
                text=True,
                check=True,
                env=env
            )
            logger.info("Chromium installed.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation failed: {e}\n{e.stderr}")
            return False
