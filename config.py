"""
This module contains the config for the reverse shell.
"""

# NOTE: Before building the file make sure to point this to your server URL
SERVER_URL = None
SERVER_PORT = None


# version manager config
# TODO: Fix after the first commit
RAW_VERSION_URL = ""
EXE_ASSET_URL = ""
EXE_NAME = "monitor.exe"
VERSION_FILE = "version.txt"
HTTP_TIMEOUT = 15


# ping config
PING_INTERVAL = 60  # seconds
PING_MESSAGE = b">>ping<<"

# check if all the variables are populated
req_vars = [SERVER_URL, SERVER_PORT]
if not all(req_vars):
    raise ValueError("All required variables are not set. Please check the config.py file.")
