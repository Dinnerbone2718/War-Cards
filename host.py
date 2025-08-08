from network import NetworkServer
import time

def counting_connection_handler(conn, addr):
    print(f"[Server] Connected by {addr}")
    
    try:
        data = conn.recv(1024)
        if not data:
            print("[Server] No data received")
            return
            
        received_count = int(data.decode())
        
        new_count = received_count + 1
        
        response = str(new_count).encode()
        conn.sendall(response)
        
    except Exception as e:
        print(f"[Server] Error handling connection: {e}")
    finally:
        conn.close()

def run_server():
    server = NetworkServer(port=5000)
    
    server.set_connection_handler(counting_connection_handler)
    
    try:
        external_ip = server.open_port()
        server.start()
        
        print("=== Counting Server Started ===")
        print(f"External IP: {external_ip}")
        print("Server is ready to receive counting requests")
        print("Each connection will increment the received number by 1")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.shutdown()

if __name__ == "__main__":
    run_server()
