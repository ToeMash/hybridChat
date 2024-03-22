import socket
import argparse

parser = argparse.ArgumentParser(
    prog='ChatServer',
    description='Server application for chat network'
)
parser.add_argument('--port')
parser.add_argument('-u', '--udp', action = 'store_true')
args = parser.parse_args()
port_int = int(args.port)

if 65535 < port_int or port_int <= 1024:
    print("Error: Port number out of bounds")
    exit()

hostname = socket.gethostname()
server_ip = socket.gethostbyname(hostname)


register_dict = {}

def do_server_tcp(): # setup socket, bind on address, wait for TCP connection and complete server actions
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
        (client_connected, client_address) = serverSocket.accept()
        
        data = client_connected.recv(1024)

        packet_type = data.decode().split('\r\n')[0]
        if packet_type == 'PROBE':
            probe_ack = "PROBEACK\r\n\r\n"
            client_connected.send(probe_ack.encode())
            client_connected.close()
        elif packet_type == 'REGISTER':
            client_connected.send(register(data).encode())
            client_connected.close()
        elif packet_type == 'BRIDGE':
            client_connected.send(bridge(data).encode())
            client_connected.close()
        elif packet_type == 'CHAT':
            chat(data)
            client_connected.close()
        elif packet_type == 'QUIT':
            cleanup(data)
            client_connected.close()
        else:
            print("ERROR: Unrecognized packet type")
    

def do_server_udp(): # setup socket, bind on address, wait for UDP packets and complete "server" actions
    print(f"Server is listening on {server_ip}:{args.port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((server_ip, port_int))
    except OSError:
        print("Error: Address already in use")
        sock.close()
        exit()
    
    while(True):
        data, client_address = sock.recvfrom(1024)

        packet_type = data.decode().split('\r\n')[0]
        if packet_type == 'PROBE':
            probe_ack = "PROBEACK\r\n\r\n"
            sock.sendto(probe_ack.encode(), client_address)
        elif packet_type == 'REGISTER':
            sock.sendto(register(data).encode(), client_address)
        elif packet_type == 'BRIDGE':
            sock.sendto(bridge(data).encode(), client_address)
        elif packet_type == 'CHAT':
            chat(data)
        elif packet_type == 'QUIT':
            sock.sendto(cleanup(data).encode(), client_address)
        else:
            print("ERROR: Unrecognized packet type")
        

def chat(data):
    data_list = data.decode().split('\r\n')
    client_id1 = data_list[1].split(' ')[1]
    client_id2 = data_list[2].split(' ')[1]
    del register_dict[client_id1]
    print(f"CLEANUP: removing {client_id1} from register\n")
    del register_dict[client_id2]
    print(f"CLEANUP: removing {client_id2} from register\n")

def cleanup(data):
    data_list = data.decode().split('\r\n')
    client_id1 = data_list[1].split(' ')[1]
    if client_id1 in register_dict.keys():
        del register_dict[client_id1]
        print(f"CLEANUP: removing {client_id1} from register\n")
    return f"QUITACK\r\nclientID: {client_id1}\r\n\r\n"

def register(data):
    data_list = data.decode().split('\r\n')
    client_id = data_list[1].split(' ')[1]
    client_ip = data_list[2].split(' ')[1]
    client_port = data_list[3].split(' ')[1]
    register_dict[client_id] = [client_ip, client_port]
    print(f"REGISTER: {client_id} from {client_ip}:{client_port} received")

    data_out = f"REGACK\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
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
        if args.udp:
            do_server_udp()
        else:
            do_server_tcp()
    except KeyboardInterrupt:
        exit()

if __name__ == "__main__":
    main()