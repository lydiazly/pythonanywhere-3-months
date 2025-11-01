# -*- coding: utf-8 -*-
# tests/test_login.py
# pytest tests/test_login.py -s
import logging
import platform

from pythonanywhere_3_months.config import Config, CREDENTIAL_ABSOLUTE_PATH
from pythonanywhere_3_months.startup import get_credentials
from pythonanywhere_3_months import run
from pythonanywhere_3_months.core import (
    PageManager,
    CURRENT_DATE_TEMPLATE,
    PEEK_MSG,
    BROWSER_CLOSED_MSG,
)


def test_login(caplog):
    """Tests logging in (chromium new headless mode)."""
    headless_shell = platform.system() == 'Linux'
    config = Config(
        peek_only=True,
        debug=False,
        test=False,
        headed_mode=False,
        browser_name='chromium',
        headless_shell=headless_shell,
    )
    credentials = get_credentials(CREDENTIAL_ABSOLUTE_PATH)
    # Check credentials
    assert (
        'username' in credentials
        and 'password' in credentials
        and credentials['username']
        and credentials['password']
    ), f"Credentials invalid: {credentials}"

    with caplog.at_level(logging.INFO):
        res = run(credentials, config)
        # Assert returns None
        assert res is None
        # Check the log records more specifically
        assert len(caplog.records) >= 5
        assert caplog.records[0].message == PageManager.LOGGED_IN_MSG
        assert caplog.records[1].message == PEEK_MSG
        assert CURRENT_DATE_TEMPLATE % '' in caplog.records[2].message
        assert caplog.records[3].message == PageManager.LOGGED_OUT_MSG
        assert caplog.records[-1].message == BROWSER_CLOSED_MSG
        print("\n" + caplog.records[2].message)
