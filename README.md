# pythonanywhere-3-months

> This is a **Playwright** version of [1337-server/pythonanywhere-3-months](https://github.com/1337-server/pythonanywhere-3-months), which was originally forked from [purarue/pythonanywhere-3-months](https://github.com/purarue/pythonanywhere-3-months) and introduced a debug option and workflows. This README is updated.

---

Logs into your [PythonAnywhere](https://www.pythonanywhere.com/) account and clicks the 'Run until 3 months from today' button, so your website doesn't deactivate automatically.

**Changes made**: Now requires Python 3.10+. Haven't tested in lower versions. No chromedriver needed. Playwright will install browsers at:
Windows: `%USERPROFILE%\AppData\Local\ms-playwright`
MacOS: `~/Library/Caches/ms-playwright`
Linux: `~/. cache/ms-playwright`

### Install and Run:

```sh
python3 -m pip install git+https://github.com/lydiazly/pythonanywhere-3-months
# Install the default browsers: Chromium, WebKit, and Firefox
playwright install
# Run
pythonanywhere_3_months -H
```

As long as no visible errors are thrown, the script succeeded. You can run it without the `-H` flag to watch it log in and click the relevant links/buttons.

```sh
usage: __main__.py [-h] [-H] [-d]

Clicks the 'Run until 3 months from today' on PythonAnywhere.

options:
  -h, --help    show this help message and exit
  -H, --hidden  Hide the browser.
  -d, --debug   Prints debug logs.
```

Put pythonanywhere credentials in your home directory; at `$XDG_DATA_HOME/pythonanywhere_credentials.yaml` (`~/.local/share/pythonanywhere_credentials.yaml`) with contents like:

```text
username: yourusername
password: 2UGArHcjfKz@9GCGuNXN
```

**Changes made**: If the file does not exist, the script will prompt the user for input then save to this path.

This also installs a command line script called `pythonanywhere_check_since` which prints nothing if `pythonanywhere_3_months` has been run in the last 2 months, but prints a reminder to run it otherwise. I have `pythonanywhere_check_since` in my `~/.zshrc` (equivalent to `~/.bashrc` or `~/.bash_profile`) file; it checks whenever I open a shell.
