# pythonanywhere-3-months-pw

[![Run](https://github.com/lydiazly/pythonanywhere-3-months/actions/workflows/run-task.yml/badge.svg?branch=master)](https://github.com/lydiazly/pythonanywhere-3-months/actions/workflows/run-task.yml)
[![python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![playwright](https://img.shields.io/badge/Playwright->=0.7.0-44BA4C)](https://playwright.dev/python)

> **Note:**
> This is a [Playwright](https://playwright.dev/python) version of [1337-server/pythonanywhere-3-months](https://github.com/1337-server/pythonanywhere-3-months), which was originally forked from [purarue/pythonanywhere-3-months](https://github.com/purarue/pythonanywhere-3-months) and introduced a debug option and scheduled workflows. Some functions work differently due to the Playwright migration. The usage in this README is updated.
>
> A GitHub Actions [workflow](https://github.com/lydiazly/pythonanywhere-3-months/actions/workflows/run-task.yml) is triggered on every push and scheduled to run every two months.
> Set your **PythonAnywhere**'s credentials:
> Go to `Settings > Secrets and variables > Actions`. Add repository secrets `USERNAME` and `PASSWORD`.
>
> Other changes made by [lydiazly](https://github.com/lydiazly):
>
> - Now requires Python >= 3.10. Haven't tested in lower versions. No `chromedriver` needed. Playwright will install browsers at:
>   - Windows: `%USERPROFILE%\AppData\Local\ms-playwright`
>   - macOS: `~/Library/Caches/ms-playwright`
>   - Linux: `~/. cache/ms-playwright`
> - If the file does not exist, the script will prompt the user for input then save to this path.
> - Options `-H` now is short for `--headed`.
> - Added options `--browser`, `--headless-shell`, and `--test`.
> - A selected browser will be installed automatically by Playwright when executing the script.
> - Changed workflows.

---

Logs into your [PythonAnywhere](https://www.pythonanywhere.com/) account and clicks the `Run until 3 months from today` button, so your website doesn't deactivate automatically.

## Install and Run

Install:

```sh
python3 -m pip install git+https://github.com/lydiazly/pythonanywhere-3-months
# Will install pythonanywhere-3-months-pw
```

Uninstall:

```sh
python3 -m pip uninstall pythonanywhere-3-months-pw
```

Put PythonAnywhere credentials at `$XDG_DATA_HOME/pythonanywhere_credentials.yaml` (`~/.local/share/pythonanywhere_credentials.yaml`) with contents like:

```text
username: your_username
password: your_password
```

Run:

```sh
pythonanywhere_3_months
```

As long as no visible errors are thrown, the script succeeded.

The default is in **headless** mode. You can run it with the `-H` or `--headed` flag to watch it log in and click the relevant links/buttons.

See help:

```sh
pythonanywhere_3_months -h
```

```text
usage: pythonanywhere_3_months [-h] [-H] [-d] [-b <browser>] [--headless-shell] [--test]

Clicks the 'Run until 3 months from today' on PythonAnywhere.

options:
  -h, --help            show this help message and exit
  -H, --headed          run in headed mode (default: headless)
  -d, --debug           print debug logs
  -b str, --browser str
                        specify a browser. Choices: chromium, firefox, webkit (default: chromium)
  --headless-shell      use a separate headless shell for chromium headless mode
  --test                test the browser without any page operation
```

---

This package also installs a command line script called `pythonanywhere_check_since` which prints nothing if `pythonanywhere_3_months` has been run in the last 2 months, but prints a reminder to run it otherwise. I have `pythonanywhere_check_since` in my `~/.zshrc` (equivalent to `~/.bashrc` or `~/.bash_profile`) file; it checks whenever I open a shell.
