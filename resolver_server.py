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

            # If query is in the cache            
            if query_lower in zone_records:
                    rec = zone_records[query_lower]
                    
                    if is_record_expired(rec, x): # If expired, remove it and treat as not found
                        del zone_records[query_lower]
                    else: # Valid record found
                        response = f"{rec['domain']},{rec['ip']},{rec['type']}"
            
            else:
                # If not we query the father server
                father_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                father_socket.sendto(data, (parent_IP, parent_Port))
                father_data, father_addr = father_socket.recvfrom(1024)
                father_response = father_data.decode().strip()

                # If we got a valid response from the father server, we cache it
                if father_response != "non-existent domain":
                    parts = [p.strip() for p in father_response.split(',', 2)]
                    name, ip_addr, rtype = parts
                    zone_records[name.lower()] = {
                        'domain': name,
                        'ip': ip_addr,           
                        'type': rtype.upper()    
                    }  
                
                response = father_response


            # Sending response back to client
            s.sendto(response.encode(), addr)