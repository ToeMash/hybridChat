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
            has_registered = True
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
            has_registered = True
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
    try:
        while time.time() < t_end:
            sock.sendto(data.encode(), server_address)
            data_out, address = sock.recvfrom(1024)
            if data_out.decode() == f"QUITACK\r\nclientID: {args.id}\r\n\r\n":
                shutdown(sock)
        shutdown(sock)
    except:
        print("Timeout, shutting down")
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
    data_out = client_socket.recv(1024)
    if data_out.decode().split('\r\n') == "REGNACK":
        print("ERROR: ID already in use, shutting down")
        shutdown(client_socket)
    client_socket.close()
    return

def register_udp(): # Sends client information to Server over UDP connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = f"REGISTER\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n"
    sock.bind(client_address)
    sock.settimeout(2)

    sock.sendto(data.encode(), server_address)
    data_out, address = sock.recvfrom(1024)
    if data_out.decode() == f"REGACK\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n":
        sock.close()
        return
    elif data_out.decode().split('\r\n')[0] == "REGNACK":
        print("ERROR: ID already in use")
        sock.close()
        return
    print(data_out.decode())
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
    target_id = data_list[1].split(':')[1]
    target_ip = data_list[2].split(':')[1].lstrip()
    target_port = data_list[3].split(':')[1].lstrip()
    if target_id == ' ': # checking for empty headers, indicates first one to bridge
        chat_target = []
        wait_tcp()
    else:
        chat_target = target_id.lstrip(), target_ip, target_port
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
    target_id = data_list[1].split(':')[1]
    target_ip = data_list[2].split(':')[1].lstrip()
    target_port = data_list[3].split(':')[1].lstrip()
    if target_id == ' ': # checking for empty headers, indicates first one to bridge
        chat_target = []
        sock.close()
        wait_udp()
    else:
        chat_target = target_id.lstrip(), target_ip, target_port
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
        data_out, chat_address = sock.recvfrom(1024)
        if not data_out:
            print("Received empty packet, shutting down")
            shutdown(sock)
        print(data_out.decode().split('\r\n')[2])
    except:
        print("Timeout: shutting down")
        shutdown(sock)
    
    try:
        for line in sys.stdin:
            if line.rstrip() == '/quit':
                data = 'QUIT\r\n\r\n'
                sock.sendto(data.encode(), chat_address)
                shutdown(sock)
            else:
                data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
                sock.sendto(data.encode(), chat_address)
            data_out, chat_address = sock.recvfrom(1024)
            if not data_out:
                print("Received empty packet, shutting down")
                shutdown(sock)
            data_list = data_out.decode().split('\r\n')
            if data_list[0] == 'QUIT':
                print("Received Response Type: QUIT - Shutting down")
                shutdown(sock)
            elif data_list[0] == 'CHAT':
                print(data_list[2])
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

    (client_connected, clientAddress) = serverSocket.accept()
    try:
        chat_packet = client_connected.recv(1024)
        chat_packet_decoded = chat_packet.decode()
        chat_pack_list = chat_packet_decoded.split('\r\n')
        if chat_pack_list[0] == 'CHAT':
            client_id = chat_pack_list[1].lstrip()
            print(f"incoming chat request from {client_id}")
        data_out = client_connected.recv(1024)
        if not data_out:
            print("Received empty packet, shutting down")
            shutdown(client_connected)
        message = data_out.decode().split('\r\n')[2]
        print(message)

        for line in sys.stdin:
            if line.rstrip() == '/quit':
                data = 'QUIT\r\n\r\n'
                client_connected.send(data.encode())
                shutdown(client_connected)
            else:
                data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
                client_connected.send(data.encode())
            data_out = client_connected.recv(1024)
            if not data_out:
                print("Received empty packet, shutting down")
                shutdown(client_connected)
            data_out = data_out.decode().split('\r\n')
            if data_out[0] == 'QUIT':
                print("Received Response Type: QUIT - Shutting down")
                shutdown(client_connected)
            elif data_out[0] == 'CHAT':
                message = data_out[2]
                print(message)
    except KeyboardInterrupt:
        shutdown(client_connected)

def chat_tcp(): # messages server to indicate a chat has begun, begins chat_loop
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)
    data_to_server = f"CHAT\r\nclientID1: {args.id}\r\nclientID2: {chat_target[0]}"
    client_socket.send(data_to_server.encode())
    client_socket.close()
    target_address = (chat_target[1], int(chat_target[2]))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(target_address)
    data = f"CHAT\r\nclientID: {args.id}\r\n\r\n"
    client_socket.send(data.encode())
    try:
        chat_loop_tcp(client_socket)
    except KeyboardInterrupt:
        shutdown(client_socket)

def chat_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(60)
    data_to_server = f"CHAT\r\nclientID1: {args.id}\r\nclientID2: {chat_target[0]}"
    sock.sendto(data_to_server.encode(), server_address)
    target_address = (chat_target[1], int(chat_target[2]))

    data = f"CHAT\r\nclientID: {args.id}\r\n\r\n\r\n"
    sock.sendto(data.encode(), target_address)
    try:
        chat_loop_udp(sock, target_address)
    except KeyboardInterrupt:
        shutdown(sock)

def chat_loop_tcp(client_socket): # Connect to other client, begin chatting
    for line in sys.stdin:
        if line.rstrip() == '/quit':
            data = 'QUIT\r\n\r\n'
            client_socket.send(data.encode())
            shutdown(client_socket)
        else:
            data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
            client_socket.send(data.encode())
        data_out = client_socket.recv(1024)
        if not data_out:
            print("Received empty packet, shutting down")
            shutdown(client_socket)
        data_list = data_out.decode().split('\r\n')
        packet_type = data_list[0]
        if packet_type == 'QUIT':
            print("Received Response Type: QUIT - Shutting down")
            shutdown(client_socket)
        elif packet_type == 'CHAT':
            message = data_list[2]
            print(message)

def chat_loop_udp(sock, chatter):
    try:
        for line in sys.stdin:
            if line.rstrip() == '/quit':
                data = 'QUIT\r\n\r\n'
                sock.sendto(data.encode(), chatter)
                shutdown(sock)
            else:
                data = f"CHAT\r\nclientID: {args.id}\r\n{line}\r\n\r\n"
                sock.sendto(data.encode(), chatter)
            data_out, addr = sock.recvfrom(1024)
            if not data_out:
                print("Received empty packet, shutting down")
                shutdown(sock)
            data_list = data_out.decode().split('\r\n')
            packet_type = data_list[0]
            if packet_type == 'QUIT':
                print("Received Response Type: QUIT - Shutting down")
                shutdown(sock)
            elif packet_type == 'CHAT':
                message = data_list[2]
                print(message)
    except TimeoutError:
        print("Timeout: shutting down")

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