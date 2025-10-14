# -*- coding: utf-8 -*-
# last_run.py
import sys
from time import time

from pythonanywhere_3_months.config import LAST_RUN_AT_ABSOLUTE_PATH


def check() -> None:
    """Checks if its been more than 2 months since the script has been run,
    reports to user on stdout.
    """
    with open(LAST_RUN_AT_ABSOLUTE_PATH) as f:
        # If last time this ran was more than 2 months ago
        if time() - float(f.read().strip()) > 5184000:
            print(
                "Its been more than 2 months since you last ran "
                "'pythonanywhere_3_months'!"
            )
            sys.exit(1)
    sys.exit(0)
