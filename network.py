import socket
import miniupnpc
import threading
import requests
import time
from typing import Optional, Callable

class NetworkServer:
    def __init__(self, port: int = 5000, description: str = "PythonGameConnection"):
        self.port = port
        self.description = description
        self.sock: Optional[socket.socket] = None
        self.upnp = miniupnpc.UPnP()
        self.external_ip: Optional[str] = None
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        self.connection_handler: Optional[Callable] = None

    def detect_nat_type(self) -> str:
        print("[NAT] Detecting NAT type...")
        try:
            self.upnp.discoverdelay = 200
            self.upnp.discover()
            self.upnp.selectigd()
            self.external_ip = self.upnp.externalipaddress()
            local_ip = self.upnp.lanaddr
            print(f"[NAT] Local IP: {local_ip}")
            print(f"[NAT] External IP: {self.external_ip}")
            if self.external_ip == local_ip:
                print("[NAT] No NAT detected (public IP assigned to device).")
                return "Open"
            self.upnp.addportmapping(self.port, 'TCP',
                                   local_ip, self.port,
                                   self.description, '')
            print("[NAT] Port mapping succeeded. Moderate NAT likely.")
            return "Moderate"
        except Exception as e:
            print(f"[NAT] Could not map port or retrieve IP properly: {e}")
            return "Strict"

    def open_port(self) -> str:
        nat_type = self.detect_nat_type()
        print(f"[UPnP] NAT Type: {nat_type}")
        if nat_type == "Strict":
            raise RuntimeError("UPnP port mapping failed — NAT is too strict.")
        print(f"[UPnP] Opening port {self.port}...")
        self.upnp.addportmapping(self.port, 'TCP',
                               self.upnp.lanaddr, self.port,
                               self.description, '')
        print(f"[UPnP] Port {self.port} opened!")
        try:
            external_ip = requests.get("https://api.ipify.org", timeout=5).text
            print(f"Access Code: {external_ip}")
            return external_ip
        except requests.RequestException as e:
            print(f"[Warning] Could not get external IP: {e}")
            return self.external_ip or "Unknown"

    def close_port(self):
        try:
            self.upnp.deleteportmapping(self.port, 'TCP')
            print(f"[UPnP] Port {self.port} closed.")
        except Exception as e:
            print(f"[UPnP] Error closing port: {e}")

    def set_connection_handler(self, handler: Callable[[socket.socket, tuple], None]):
        self.connection_handler = handler

    def default_connection_handler(self, conn: socket.socket, addr: tuple):
        print(f"[Server] Connected by {addr}")
        try:
            conn.sendall(b"Hello Jacob. Welcome to the matrix")
        except Exception as e:
            print(f"[Server] Error sending data: {e}")
        finally:
            conn.close()

    def _server_loop(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(('', self.port))
            self.sock.listen(5)
            print(f"[Server] Listening on port {self.port}...")
            while self.is_running:
                try:
                    self.sock.settimeout(1.0)
                    conn, addr = self.sock.accept()
                    handler = self.connection_handler or self.default_connection_handler
                    handler(conn, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        print(f"[Server] Error accepting connection: {e}")
        except Exception as e:
            print(f"[Server] Server error: {e}")
        finally:
            if self.sock:
                self.sock.close()
                self.sock = None

    def start(self):
        if self.is_running:
            print("[Server] Server is already running.")
            return
        self.is_running = True
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()

    def stop(self):
        if not self.is_running:
            print("[Server] Server is not running.")
            return
        print("[Server] Stopping server...")
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        if self.sock:
            self.sock.close()
            self.sock = None

    def shutdown(self):
        self.stop()
        self.close_port()
        print("[Server] Server shutdown complete.")

class NetworkClient:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def connect_to_server(self, ip: str, port: int, message_handler: Optional[Callable[[bytes], None]] = None):
        print(f"[Client] Connecting to {ip}:{port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((ip, port))
                data = sock.recv(1024)
                if message_handler:
                    message_handler(data)
                else:
                    print(f"[Client] Received: {data.decode()}")
                return data
        except socket.timeout:
            print(f"[Client] Connection timeout after {self.timeout} seconds")
            raise
        except ConnectionRefusedError:
            print(f"[Client] Connection refused to {ip}:{port}")
            raise
        except Exception as e:
            print(f"[Client] Connection error: {e}")
            raise

    def send_message(self, ip: str, port: int, message: bytes):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((ip, port))
                sock.sendall(message)
                response = sock.recv(1024)
                return response
        except Exception as e:
            print(f"[Client] Error sending message: {e}")
            raise