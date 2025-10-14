# -*- coding: utf-8 -*-
# tests/test_browser.py
# pytest tests/test_browser.py --browser-channel chromium
import logging

from pythonanywhere_3_months.config import Config
from pythonanywhere_3_months import run
from pythonanywhere_3_months.core import TEST_MSG, CLOSED_MSG


def test_chromium(caplog):
    """Tests launching chromium (new headless mode)."""
    config = Config(
        peek_only=False,
        debug=False,
        test=True,
        headed_mode=False,
        browser_name='chromium',
        headless_shell=False,
    )
    credentials = {}  # dummy

    with caplog.at_level(logging.INFO):
        res = run(credentials, config)
        # Assert returns None
        assert res is None
        # Check the log records more specifically
        assert len(caplog.records) == 2
        assert caplog.records[0].message == TEST_MSG
        assert caplog.records[-1].message == CLOSED_MSG
