# -*- coding: utf-8 -*-
# cli.py
"""CLI interface and main entry point."""
import sys

from pythonanywhere_3_months.config import (
    CREDENTIAL_ABSOLUTE_PATH,
    load_config,
)
from pythonanywhere_3_months.startup import (
    get_args_and_logger,
    get_credentials,
)
from pythonanywhere_3_months.core import run


def main() -> None:
    """Gets CLI arguments and runs application."""
    try:
        args, logger = get_args_and_logger()
        credentials = get_credentials(CREDENTIAL_ABSOLUTE_PATH, logger)
        config = load_config(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        run(credentials, config, logger)
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception:
        sys.exit(1)
