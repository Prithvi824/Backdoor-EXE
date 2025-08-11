"""
This module contains the config for the reverse shell.
"""

# NOTE: Before building the file make sure to point this to your server URL
SERVER_URL = None
SERVER_PORT = None


# version manager config
CURRENT_VERSION = "1.0.0"
RAW_VERSION_URL = "https://raw.githubusercontent.com/Prithvi824/Backdoor-EXE/refs/heads/main/version.txt"
HTTP_TIMEOUT = 60
UPDATER_EXE_URL = "https://github.com/Prithvi824/Backdoor-EXE/raw/refs/heads/main/dist/updater.exe"


# ping config
PING_INTERVAL = 180  # seconds
PING_MESSAGE = b">>ping<<"

# check if all the variables are populated
req_vars = [SERVER_URL, SERVER_PORT]
if not all(req_vars):
    raise ValueError("All required variables are not set. Please check the config.py file.")
