import sys
from . import credential_file_name
from .helpers import get_options, get_credentials
from .core import run


def main():
    """Gets options, runs program, cleans up selenium on exception."""
    args, logger = get_options()
    credentials = get_credentials(credential_file_name, logger)
    success = run(credentials, args, logger)
    if success:
        print("Done!", file=sys.stderr)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
