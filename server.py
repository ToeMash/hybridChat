import socket
import argparse
import sys

parser = argparse.ArgumentParser(
    prog='ChatServer',
    description='Server application for chat network'
)
parser.add_argument('--port')
args = parser.parse_args()
port_int = int(args.port)

if 65535 < port_int or port_int <= 1024:
    print("Error: Port number out of bounds")
    exit()

hostname = socket.gethostname()
server_ip = socket.gethostbyname(hostname)


register_dict = {}

def do_server():
    print(f"Server is listening on {server_ip}:{args.port}")
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        serverSocket.bind((server_ip, port_int))
    except OSError:
        print("Error: Address already in use")
        serverSocket.close()
        exit()
    serverSocket.listen()

    
    while(True):
        (clientConnected, clientAddress) = serverSocket.accept()
        
        dataFromClient = clientConnected.recv(1024)

        packet_type = dataFromClient.decode().split('\r\n')[0]
        if packet_type == 'REGISTER':
            clientConnected.send(register(dataFromClient).encode())
            clientConnected.close()
        elif packet_type == 'BRIDGE':
            clientConnected.send(bridge(dataFromClient).encode())
            clientConnected.close()
        else:
            print("ERROR: Unrecognized packet type") #TEST TO FIND OUT THE RIGHT RESPONSE
    
    


def register(data):
    data_list = data.decode().split('\r\n')
    client_id = data_list[1].split(' ')[1]
    client_ip = data_list[2].split(' ')[1]
    client_port = data_list[3].split(' ')[1]
    register_dict[client_id] = [client_ip, client_port]
    print(f"REGISTER: {client_id} from {client_ip}:{client_port} received")

    data_out = "REGACK\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
    return data_out

def bridge(data):
    data_list = data.decode().split('\r\n')
    client_id = data_list[1].split(' ')[1]
    if len(register_dict) > 1:
        client = list(register_dict.keys())[0]
        data_out = f"BRIDGEACK\r\nclientID: {client}\r\nIP: {register_dict[client][0]}\r\nPort: {register_dict[client][1]}\r\n\r\n"
    else:
        data_out = "BRIDGEACK\r\nclientID: \r\nIP: \r\nPort: \r\n\r\n"
    print(f"BRIDGE  : {client_id} {register_dict[client_id][0]}:{register_dict[client_id][1]}")
    return data_out

def main():
    try:
        do_server()
    except KeyboardInterrupt:
        exit()

if __name__ == "__main__":
    main()