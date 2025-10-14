# __init__.py
"""A Playwright version of pythonanywhere-3-months.
Logs into your PythonAnywhere account and extend the expiry date.
"""

__all__ = ['run', 'check']
__version__ = '0.2.1'
__author__ = 'Lydia Zhang'

from pythonanywhere_3_months.core import run
from pythonanywhere_3_months.last_run import check
