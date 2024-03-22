import socket
import argparse
import sys
import time

parser = argparse.ArgumentParser(
    prog='ChatClient',
    description='Client application for chat network'
)
parser.add_argument('--id')
parser.add_argument('--port')
parser.add_argument('--server')
args = parser.parse_args()

if 65535 < int(args.port) <= 1024:
    print("Error: Port out of bounds")
    exit()

server_ip, server_port = args.server.split(':')
hostname = socket.gethostname()
client_ip = socket.gethostbyname(hostname)
server_address = (server_ip, int(server_port))
client_address = (client_ip, int(args.port))

global chat_target 
chat_target = []

def probe():
    data = "PROBE\r\n\r\n"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(server_address)
        client_socket.send(data.encode())
        dataFromServer = client_socket.recv(1024)
        if dataFromServer: 
            return 0
    except socket.error:
        client_socket.close()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(client_address)
    sock.settimeout(2)
    t_end = time.time() + 2
    while time.time() < t_end:
        try:
            sock.sendto(data.encode(), server_address)
            data_out, address = sock.recvfrom(1024)
            if data_out is not None:
                sock.close()
                return 1
        except:
            sock.close()
            return -1
    return -1

def get_input_tcp(): # Terminal input loop for TCP server
    has_registered = False
    for line in sys.stdin:
        if line.rstrip() == '/id':
            print(args.id)
        elif line.rstrip() == '/register':
            register_tcp()
        elif line.rstrip() == '/bridge' and has_registered:
            bridge_tcp()
        elif line.rstrip() == '/chat' and len(chat_target) > 0:
            chat_tcp()
        elif line.rstrip() == '/quit':
            quit_tcp()
        else:
            print("bad input")

def get_input_udp(): # Terminal input loop for TCP server
    has_registered = False
    for line in sys.stdin:
        if line.rstrip() == '/id':
            print(args.id)
        elif line.rstrip() == '/register':
            register_udp()
        elif line.rstrip() == '/bridge' and has_registered:
            bridge_udp()
        elif line.rstrip() == '/chat' and len(chat_target) > 0:
            chat_udp()
        elif line.rstrip() == '/quit':
            quit_udp()
        else:
            print("bad input")

def quit_tcp(): # Sends a quit packet to server over TCP before shutting down
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(server_address)
    except socket.error:
        print("Socket Error: failed to connect")
        shutdown(client_socket)
    data = f"QUIT\r\nclientID: {args.id}\r\n\r\n"
    client_socket.send(data.encode())
    shutdown(client_socket)

def quit_udp(): # Sends a quit packet to server over UDP before shutting down
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = f"QUIT\r\nclientID: {args.id}\r\n\r\n"
    sock.bind(client_address)
    sock.settimeout(2)
    t_end = time.time() + 2
    while time.time() < t_end:
        sock.sendto(data.encode(), server_address)
        data_out, address = sock.recvfrom(1024)
        if data_out.decode() == f"QUITACK\r\nclientID: {args.id}\r\n\r\n":
            shutdown(sock)
    shutdown(sock)


def register_tcp(): # Sends client information to Server over TCP connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(server_address)
    except socket.error:
        print("Socket Error: failed to connect")
        shutdown(client_socket)
    data = f"REGISTER\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n"
    client_socket.send(data.encode())
    dataFromServer = client_socket.recv(1024)
    client_socket.close()
    return

def register_udp(): # Sends client information to Server over UDP connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = f"REGISTER\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n"
    sock.bind(client_address)
    sock.settimeout(2)

    t_end = time.time() + 5
    while time.time() < t_end:
        sock.sendto(data.encode(), server_address)
        data_out, address = sock.recvfrom(1024)
        if data_out.decode() == f"REGACK\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n":
            sock.close()
            return
    print("Error: No response from server")
    shutdown(sock)

def bridge_tcp(): # Begins bridge with server, if no other chatters online, enter wait, else receive other client info for connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, int(server_port)))
    except socket.error:
        print("Socket Error: failed to connect")
        shutdown(client_socket)
    data = f"BRIDGE\r\nclientID: {args.id}\r\n\r\n"
    client_socket.send(data.encode())
    dataFromServer = client_socket.recv(1024)
    data_out = dataFromServer.decode()
    print(data_out)
    data_list = data_out.split('\r\n')
    global chat_target
    if data_list[1].split(':')[1] == ' ':
        chat_target = []
        wait_tcp()
    else:
        chat_target = data_list[1].split(':')[1].lstrip(), data_list[2].split(':')[1].lstrip(), data_list[3].split(':')[1].lstrip()
    client_socket.close()
    return

def bridge_udp(): # same as bridge_tcp() but over UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(client_address)
    sock.settimeout(2)
    data = f"BRIDGE\r\nclientID: {args.id}\r\n\r\n"

    sock.sendto(data.encode(), server_address)
    data_out, address = sock.recvfrom(1024)
    data_text = data_out.decode()
    print(data_text)
    data_list = data_text.split('\r\n')
    global chat_target
    if data_list[1].split(':')[1] == ' ':
        chat_target = []
        wait_udp()
    else:
        chat_target = data_list[1].split(':')[1].lstrip(), data_list[2].split(':')[1].lstrip(), data_list[3].split(':')[1].lstrip()
    sock.close()
    return
        
def wait_udp(): # waits for another client to send a message
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(60)
    try:
        sock.bind(client_address)
    except OSError:
        print("Error: Address already in use")
        shutdown()
    try:
        chat_packet, chat_address = sock.recvfrom(1024)
        chat_text = chat_packet.decode()
        chat_list = chat_text.split('\r\n')
        if chat_list[0] == 'CHAT':
            client_id = chat_list[0].lstrip()
            print(f"incoming chat request from {client_id}")
    except:
        shutdown(sock)
    try:
        chat_packet, chat_address = sock.recvfrom(1024)
    except:
        shutdown(sock)

def wait_tcp(): # Sets up client as server and waits for another client to connect
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        serverSocket.bind(client_address)
    except OSError:
        print("Error: Address already in use")
        shutdown()
    serverSocket.listen()

    (clientConnected, clientAddress) = serverSocket.accept()
    try:
        chat_packet = clientConnected.recv(1024)
        chat_packet_decoded = chat_packet.decode()
        chat_pack_list = chat_packet_decoded.split('\r\n')
        if chat_pack_list[0] == 'CHAT':
            client_id = chat_pack_list[1].lstrip()
            print(f"incoming chat request from {client_id}")
        dataFromClient = clientConnected.recv(1024)
        if not dataFromClient:
            print("Received empty packet, shutting down")
            shutdown(clientConnected)
        print(dataFromClient.decode().split('\r\n')[2])

        for line in sys.stdin:
            if line.rstrip() == '/quit':
                data = 'QUIT\r\n\r\n'
                clientConnected.send(data.encode())
                shutdown(clientConnected)
            else:
                data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
                clientConnected.send(data.encode())
            dataFromClient = clientConnected.recv(1024)
            if not dataFromClient:
                print("Received empty packet, shutting down")
                shutdown(clientConnected)
            data_out = dataFromClient.decode().split('\r\n')
            if data_out[0] == 'QUIT':
                print("Received Response Type: QUIT - Shutting down")
                shutdown(clientConnected)
            elif data_out[0] == 'CHAT':
                print(data_out[2])
    except KeyboardInterrupt:
        shutdown(clientConnected)

def chat_tcp(): # messages server to indicate a chat has begun, begins chat_loop
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(server_address)
    data = f"CHAT\r\nclientID1: {args.id}\r\nclientID2: {chat_target[0]}"

    clientSocket.connect((chat_target[1], int(chat_target[2])))
    data = f"CHAT\r\nclientID: {args.id}\r\n\r\n\r\n"
    clientSocket.send(data.encode())
    try:
        chat_loop_tcp(clientSocket)
    except KeyboardInterrupt:
        shutdown(clientSocket)

def chat_loop_tcp(clientSocket): # Connect to other client, begin chatting
    for line in sys.stdin: # chat loop
        if line.rstrip() == '/quit':
            data = 'QUIT\r\n\r\n'
            clientSocket.send(data.encode())
            shutdown(clientSocket)
        else:
            data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
            clientSocket.send(data.encode())
        dataFromServer = clientSocket.recv(1024)
        if not dataFromServer:
            print("Received empty packet, shutting down")
            shutdown(clientSocket)
        data_out = dataFromServer.decode().split('\r\n')
        if data_out[0] == 'QUIT':
            print("Received Response Type: QUIT - Shutting down")
            shutdown(clientSocket)
        elif data_out[0] == 'CHAT':
            print(data_out[2])

def shutdown(socket=None):
    if socket:
        socket.close()
    exit()

def main():
    protocol = probe()
    if protocol == 0:
        print(f"{args.id} running on {client_ip} over TCP")
        while True:
            get_input_tcp()
    elif protocol == 1:
        print(f"{args.id} running on {client_ip} over UDP")
        while True:
            get_input_udp()
    else:
        print("Server is not online, shutting down")
        shutdown()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        shutdown()
    shutdown()