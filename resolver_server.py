import socket
import sys
import time

def is_record_expired(rec, ttl_x):
    """Checks if the record has expired based on the TTL (x seconds)."""
    # Assuming 'timestamp' is stored in the record
    return time.time() - rec.get('timestamp', 0) > ttl_x

if __name__ == '__main__':
    

       

    my_port = int(sys.argv[1])
    parent_IP = sys.argv[2]
    parent_Port = int(sys.argv[3])
    x = int(sys.argv[4])

    # Set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    s.bind(('', my_port)) 

    # To save records we got from the father server
    zone_records = {}

    # Main loop for listening
    while True:
            data, addr = s.recvfrom(1024)  
            
            # We format the input to match our search keys
            query = data.decode().strip()     
            query_lower = query.lower()
            response = None

            # If query is in the cache            
            if query_lower in zone_records:
                    rec = zone_records[query_lower]
                    
                    if is_record_expired(rec, x): # If expired, remove it and treat as not found
                        del zone_records[query_lower]
                    else: # Valid record found
                        response = f"{rec['domain']},{rec['ip']},{rec['type']}"
            
            else:
                if response is None:
                    current_server_ip = parent_IP
                    current_server_port = parent_Port
                    while True:
                        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        temp_socket.settimeout(3.0) 
                        temp_socket.sendto(data, (current_server_ip, current_server_port))
                        temp_data, _ = temp_socket.recvfrom(1024)
                        server_response = temp_data.decode().strip()
                        temp_socket.close()

                        response = server_response
                    

                        # If we got a valid response from the father server, we cache it
                        if response != "non-existent domain":
                            parts = [p.strip() for p in response.split(',', 2)]
                            name, ip_addr, rtype = parts
                            # We cache the result
                            zone_records[name.lower()] = {
                                'domain': name,
                                'ip': ip_addr,           
                                'type': rtype.upper(),
                                'timestamp': time.time()    
                            }  
                            if rtype.upper() == 'A':
                                break  # We got an A record, we are done
                            elif rtype.upper() == 'NS':
                                 if ':' in ip_addr:
                                        current_server_ip, current_server_port = ip_addr.split(':')
                                        current_server_port = int(current_server_port)
                                 else:
                                        current_server_ip = ip_addr
                                        current_server_port = 53  
                        else:
                             break 
            # Sending response back to client
            s.sendto(response.encode(), addr)