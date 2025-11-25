import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto('elad katz'.encode(), ('127.0.0.1', 55555))

data, addr = s.recvfrom(1024)
print(data.decode())

s.close()