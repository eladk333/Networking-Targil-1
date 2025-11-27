import socket
import sys

if __name__ == '__main__':

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

     # Set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query_domain = sys.stdin.readline().strip()
    


    s.sendto(query_domain.encode(), (server_ip, server_port))

    data, addr = s.recvfrom(1024)
    response = data.decode().strip()
    if response == "non-existent domain":
                print("non-existent domain")
    else:
            parts = response.split(',', 2)
            ip_address = parts[1].strip()
            print(ip_address)
            
    s.close()