"""version_manager.py

Class-based updater for the packaged application (`monitor.exe`).
It compares the local `version.txt` to the remote one on GitHub and, when a
newer version exists, stages a replacement executable next to the currently
running file. The actual overwrite happens on the next launch to avoid file-
lock issues on Windows.
"""

from __future__ import annotations

# 1st party imports
import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# 3rd party imports
import requests

# local imports
from config import RAW_VERSION_URL, CURRENT_VERSION, HTTP_TIMEOUT, UPDATER_EXE_URL

# the file name of the updater
UPDATER_EXE = "updater.exe"


class VersionManager:
    """Encapsulates all version-handling logic."""

    def check_and_update(self) -> bool:
        """Return True if an update was downloaded and staged."""

        # get the local and remote version
        local = CURRENT_VERSION
        remote = self._fetch_remote_version()

        # if remote version is newer
        if self._is_remote_newer(remote, local):
            return True
        return False

    def _fetch_remote_version(self) -> Optional[str]:
        """
        Fetch the remote version from the raw version url.

        Returns:
            Optional[str]: The remote version if found, CURRENT_VERSION otherwise.
        """

        try:

            # get the remote version
            response = requests.get(RAW_VERSION_URL, timeout=HTTP_TIMEOUT)

            # raise an exception if the request failed
            response.raise_for_status()

            # return the remote version
            return response.text.strip()

        except Exception:
            return CURRENT_VERSION

    def _version_tuple(self, v: str) -> Tuple[int, ...]:
        """Convert a version string to a tuple of integers.

        Args:
            v (str): The version string to convert.

        Returns:
            Tuple[int, ...]: The version tuple.
        """

        # get the parts of the version
        parts = [int(p) if p.isdigit() else 0 for p in v.split(".")]

        # make sure the version has 3 parts
        while len(parts) < 3:
            parts.append(0)

        # return the version tuple
        return tuple(parts[:3])

    def _is_remote_newer(self, remote: str, local: str) -> bool:
        """Check if the remote version is newer than the local version.

        Args:
            remote (str): The remote version.
            local (str): The local version.

        Returns:
            bool: True if the remote version is newer, False otherwise.
        """

        # return the comparison result
        return self._version_tuple(remote) > self._version_tuple(local)

    def stage_new_update(self) -> None:
        """
        Download and run the updater from the github repo.
        This function should be called when a new update is available.
        """

        # download the updater executable
        updater_path = self._download_updater()

        # if the updater path is not found
        if not updater_path:
            return None

        # run the updater in background and exit
        # NOTE: format: updater.exe <current_exe>
        subprocess.Popen(
            [str(updater_path), sys.executable],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        sys.exit(0)

    def _download_updater(self) -> Optional[Path]:
        """
        Download the updater from the github repo.

        Returns:
            Optional[Path]: The path to the downloaded updater.
        """

        try:

            # make the request
            response = requests.get(UPDATER_EXE_URL, timeout=HTTP_TIMEOUT)

            # raise an exception if the request failed
            response.raise_for_status()

            # save the file
            with open(UPDATER_EXE, "wb") as f:
                f.write(response.content)

        except Exception:
            return None

        # return the path
        return Path(UPDATER_EXE)

    def _app_dir(self) -> Path:
        """
        This function returns the directory containing the running exe.

        Returns:
            Path: The directory containing the running exe.
        """

        # if the app is frozen
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent

        # else return the path of the current file
        return Path(__file__).resolve().parent

    def remove_local_updater(self) -> None:
        """
        This function check if a updater.exe exists and remove it.
        """

        # get the path
        updater_path = self._app_dir() / UPDATER_EXE

        # remove the updater
        if updater_path.exists():
            os.remove(updater_path)
