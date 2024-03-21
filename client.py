import socket
import argparse
import sys

parser = argparse.ArgumentParser(
    prog='ChatClient',
    description='Client application for chat network'
)
parser.add_argument('--id')
parser.add_argument('--port')
parser.add_argument('--server')
args = parser.parse_args()

if 65535 < int(args.port) <= 1024:
    print("Error: Port number out of bounds")
    exit()

server_ip, server_port = args.server.split(':')
hostname = socket.gethostname()
client_ip = socket.gethostbyname(hostname)

global chat_target 
chat_target = []

def get_input(): # Terminal input loop
    has_registered = False
    for line in sys.stdin:
        if line.rstrip() == '/id':
            print(args.id)
        elif line.rstrip() == '/register':
            register()
            has_registered = True
        elif line.rstrip() == '/bridge' and has_registered:
            bridge()
        elif line.rstrip() == '/chat' and len(chat_target) > 0:
            chat()
        else:
            print("bad input")

def register(): # Sends client information to Server
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((server_ip, int(server_port)))
    except socket.error:
        print("Socket Error: failed to connect")
        #print(f"attempted to connect to {server_ip}:{server_port}")
        shutdown(clientSocket)
    data = f"REGISTER\r\nclientID: {args.id}\r\nIP: {client_ip}\r\nPort: {args.port}\r\n\r\n"
    clientSocket.send(data.encode())
    dataFromServer = clientSocket.recv(1024)
    clientSocket.close()
    return

def bridge(): # Begins bridge with server, if no other chatters online, enter wait, else receive other client info for connection
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((server_ip, int(server_port)))
    except socket.error:
        print("Socket Error: failed to connect")
        shutdown(clientSocket)
    data = f"BRIDGE\r\nclientID: {args.id}\r\n\r\n"
    clientSocket.send(data.encode())
    dataFromServer = clientSocket.recv(1024)
    data_out = dataFromServer.decode()
    print(data_out)
    data_list = data_out.split('\r\n')
    #print(f"data_list = {data_list}")
    global chat_target
    if data_list[1].split(':')[1] == ' ':
        chat_target = []
        wait()
    else:
        chat_target = data_list[1].split(':')[1].lstrip(), data_list[2].split(':')[1].lstrip(), data_list[3].split(':')[1].lstrip()
    clientSocket.close()
    return

def wait(): # Sets up client as server and waits for another client to connect
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        serverSocket.bind((client_ip, int(args.port)))
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

def chat(): # begins chat_loop
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((chat_target[1], int(chat_target[2])))
    data = f"CHAT\r\nclientID: {args.id}\r\n\r\n\r\n"
    clientSocket.send(data.encode())
    try:
        chat_loop(clientSocket)
    except KeyboardInterrupt:
        shutdown(clientSocket)

def chat_loop(clientSocket): # Connect to other client, begin chatting
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
    print(f"{args.id} running on {client_ip}")
    while True:
        get_input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        shutdown()
    shutdown()