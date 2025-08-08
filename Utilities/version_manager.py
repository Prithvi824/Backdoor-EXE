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
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Optional

# 3rd party imports
import requests

# local imports
from config import RAW_VERSION_URL, EXE_ASSET_URL, EXE_NAME, VERSION_FILE, HTTP_TIMEOUT


class VersionManager:
    """Encapsulates all update-handling logic."""

    def check_and_update(self) -> bool:
        """Return True if an update was downloaded and staged."""

        # get the local and remote version
        local = self._read_local_version()
        remote = self._fetch_remote_version()

        # if remote version is not found
        if not remote:
            return False

        # if remote version is newer
        if self._is_remote_newer(remote, local):
            self._stage_new_exe()
            return True
        return False

    def _app_dir(self) -> Path:
        """Directory containing the running exe and version.txt"""

        # if the app is frozen
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent

        # else return the path of the current file
        return Path(__file__).resolve().parent

    def _read_local_version(self) -> str:
        """Read the local version.txt file and get the version.

        Returns:
            str: The version of the application.
        """

        # get the path
        path = self._app_dir() / VERSION_FILE

        # check if the file exists
        if not path.exists():
            return "0.0.0"

        # return the version
        return path.read_text(encoding="utf-8").strip()

    def _fetch_remote_version(self) -> Optional[str]:
        """Fetch the remote version from the raw version url.

        Returns:
            Optional[str]: The remote version if found, None otherwise.
        """

        try:

            # get the remote version
            response = requests.get(RAW_VERSION_URL, timeout=HTTP_TIMEOUT)

            # raise an exception if the request failed
            response.raise_for_status()

            # return the remote version
            return response.text.strip()

        except Exception:
            return None

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

    def _download_latest_exe(self) -> Path:
        """Download the latest executable from the remote URL.

        Returns:
            Path: The path to the downloaded executable.
        """

        # download the latest executable
        with requests.get(EXE_ASSET_URL, stream=True, timeout=HTTP_TIMEOUT) as r:

            # raise an exception if the request failed
            r.raise_for_status()

            # create a temporary file
            fd, tmp = tempfile.mkstemp(suffix=".exe")
            os.close(fd)

            # save the file
            with open(tmp, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        # return the path
        return Path(tmp)

    def _stage_new_exe(self) -> None:
        """Stage the new executable for replacement."""

        # download the latest executable
        new_exe_tmp = self._download_latest_exe()

        # get the target path
        target = self._app_dir() / EXE_NAME

        # get the staged path
        staged = target.with_suffix(".new")

        # stage the new executable
        try:
            new_exe_tmp.replace(staged)
        finally:

            # remove the temporary file
            if new_exe_tmp.exists():
                new_exe_tmp.unlink(missing_ok=True)

    @staticmethod
    def apply_staged_update() -> None:
        """Call early in program start to swap .new file into place, if present.
        This function should be called early in program start to swap .new file into place, if present.
        """

        # get the path
        exe_path = Path(sys.executable).resolve()

        # get the staged path
        staged = exe_path.with_suffix(".new")

        # if the staged file exists
        if staged.exists():

            # create a backup
            backup = exe_path.with_suffix(".bak")
            try:

                # replace the executable
                exe_path.replace(backup)
                staged.replace(exe_path)
            finally:

                # remove the backup
                if backup.exists():
                    backup.unlink(missing_ok=True)
