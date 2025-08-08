"""
This module contains the commands for the reverse shell.
"""

# 1st party imports
from enum import Enum

BASE_PREFIX = "use"


class Utils(Enum):
    """
    The Available utils for the reverse shell.
    """

    PHOTOGRAPHER = "photographer"
    UI_MANAGER = "ui_manager"
    FILE_MANAGER = "file_manager"


class ShellCommands(Enum):
    """
    The commands for the reverse shell. A space is added in commands which takes arguments
    """

    TAKE_SCREENSHOT = "take-screenshot"
    EXIT_SHELL = "exit-shell"
    LEFT_CLICK = "left-click"
    RIGHT_CLICK = "right-click"
    CLICK_X_Y_LEFT = "click-x-y-left"
    CLICK_X_Y_RIGHT = "click-x-y-right"
    SWITCH_TAB = "switch-tab"
    SHOW_DESKTOP = "show-desktop"
    TYPE_SENTENCE = "type-sentence"
    SCROLL_MOUSE = "scroll-mouse"
    PERFORM_COMBO = "perform-combo"
    UPLOAD_FILE = "upload-file"
