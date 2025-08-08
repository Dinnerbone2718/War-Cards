from network import NetworkClient
import time

if __name__ == "__main__":
    client = NetworkClient(timeout=5.0)
    
    server_ip = "73.134.112.7"
    server_port = 5000
    
    current_count = 1
    
    try:
        print(f"[Client] Starting count exchange with server at {server_ip}:{server_port}")
        
        while current_count <= 1000:
            print(f"[Client] Sending count: {current_count}")
            
            message = str(current_count).encode()
            response = client.send_message(server_ip, server_port, message)
            
            received = (response.decode())
            print(f"[Client] Received: {received}")

            current_count += 1
            

            

            
        print(f"\n[Client] Final count reached: {current_count}")
        
    except Exception as e:
        print(f"[Client] Error during counting: {e}")