# pythonanywhere-3-months

> This is a forked version of [1337-server/pythonanywhere-3-months](https://github.com/1337-server/pythonanywhere-3-months), which was originally forked from [purarue/pythonanywhere-3-months](https://github.com/purarue/pythonanywhere-3-months) but contains debug option and scheduled workflows. This README is updated.

Logs into your [PythonAnywhere](https://www.pythonanywhere.com/) account and clicks the 'Run until 3 months from today' button, so your website doesn't deactivate automatically.

Requires: Python 3.6+ and a chromedriver binary. See [here](https://gist.github.com/purarue/709a824b8c56ea22dbf4e86a7804287d) for chromedriver.

**Changes made**: Now requires Python 3.10+. Haven't tested in lower versions.

#### Install and Run:

```sh
python3 -m pip install git+https://github.com/lydiazly/pythonanywhere-3-months
pythonanywhere_3_months -Hc /usr/local/bin/chromedriver
```

As long as no visible errors are thrown, the script succeeded. You can run it without the `-H` flag to watch it log in and click the relevant links/buttons.

```sh
usage: __main__.py [-h] [-H] [-c CHROMEDRIVER_PATH] [-d]

Clicks the 'Run until 3 months from today' on PythonAnywhere.

options:
  -h, --help            show this help message and exit
  -H, --hidden          Hide the ChromeDriver.
  -c CHROMEDRIVER_PATH, --chromedriver-path CHROMEDRIVER_PATH
                        Provides the location of ChromeDriver. Should probably be the full path.
  -d, --debug           Prints debug logs.
```

Put pythonanywhere credentials in your home directory; at `$XDG_DATA_HOME/pythonanywhere_credentials.yaml` (`~/.local/share/pythonanywhere_credentials.yaml`) with contents like:

```text
username: yourusername
password: 2UGArHcjfKz@9GCGuNXN
```

**Changes made**: If the file does not exist, the script will prompt the user to input them.

This also installs a command line script called `pythonanywhere_check_since` which prints nothing if `pythonanywhere_3_months` has been run in the last 2 months, but prints a reminder to run it otherwise. I have `pythonanywhere_check_since` in my `~/.zshrc` (equivalent to `~/.bashrc` or `~/.bash_profile`) file; it checks whenever I open a shell.
