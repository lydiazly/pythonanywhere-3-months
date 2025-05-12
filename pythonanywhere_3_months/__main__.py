import sys
from . import credential_file_name
from .core import get_options, get_credentials, run


def main():
    """Gets options, runs program, cleans up selenium on exception."""
    headless, logger = get_options()
    username_or_email_address, password = get_credentials(credential_file_name)
    success = run(username_or_email_address, password, headless, logger)
    if success:
        print("Done!", file=sys.stderr)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
