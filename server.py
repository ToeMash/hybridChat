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

suspect_ips = {}

banned_ips = []

def do_server_tcp():
    ''' Setup socket, bind on address, wait for TCP connection and complete server actions '''
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
        if client_address[0] in banned_ips:
            client_connected.close()
            continue
        else:
            if client_address[0] in suspect_ips:
                suspect_ips[client_address[0]] = suspect_ips[client_address[0]] + 1
                if suspect_ips[client_address[0]] > 10:
                    del suspect_ips[client_address[0]]
                    banned_ips.append(client_address[0])
            else:
                suspect_ips[client_address[0]] = 1
        
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
        print(register_dict) # for dev
    

def do_server_udp():
    ''' setup socket, bind on address, wait for UDP packets and complete server actions '''
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
        if client_address[0] in banned_ips:
            continue # No way to block packets, but stops the server from processing it
        else:
            if client_address[0] in suspect_ips:
                suspect_ips[client_address[0]] = suspect_ips[client_address[0]] + 1
                if suspect_ips[client_address[0]] > 10:
                    del suspect_ips[client_address[0]]
                    banned_ips.append(client_address[0])
            else:
                suspect_ips[client_address[0]] = 1

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
        print(register_dict) # for dev
        

def chat(data):
    ''' Parses CHAT packet, removing clients from the register and removes them from suspect_ips. 
    Parameters
    ----------
    data : packet
        The incoming packet to be parsed'''
    data_list = data.decode().split('\r\n')
    client_id1 = data_list[1].split(' ')[1]
    client_id2 = data_list[2].split(' ')[1]

    client_ip1 = register_dict[client_id1][0]
    client_ip2 = register_dict[client_id2][0]

    if client_ip1 in suspect_ips:
        del suspect_ips[client_ip1] # we clear an IP from being suspicious once it successfully engages in a chat
    if client_ip2 in suspect_ips:
        del suspect_ips[client_ip2]
    print(f"CLEANUP: removing {client_id1} from register\n")
    del register_dict[client_id1]
    del register_dict[client_id2]
    print(f"CLEANUP: removing {client_id2} from register\n")

def cleanup(data):
    ''' Parses a QUIT packet, removing the client from the register.
    Parameters
    ----------
    data : packet
        The incoming packet to be parsed'''
    data_list = data.decode().split('\r\n')
    client_id1 = data_list[1].split(' ')[1]
    if client_id1 in register_dict.keys():
        del register_dict[client_id1]
        print(f"CLEANUP: removing {client_id1} from register\n")
    return f"QUITACK\r\nclientID: {client_id1}\r\n\r\n"

def register(data):
    ''' Parses a REGISTER packet, and places the client information into the register. If the client_id is already registered, returns a REGNACK message, else returns a REGACK message.
    Parameters
    ----------
    data : packet
        The incoming packet to be parsed'''
    data_list = data.decode().split('\r\n')
    client_id = data_list[1].split(' ')[1]
    client_ip = data_list[2].split(' ')[1]
    client_port = data_list[3].split(' ')[1]

    if client_id in register_dict.keys():
        data_out = "REGNACK\r\n\r\n"
        print(f"REGISTER ERROR: Client ID already in use")
    else:
        register_dict[client_id] = [client_ip, client_port]
        print(f"REGISTER: {client_id} from {client_ip}:{client_port} received")
        data_out = f"REGACK\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
    return data_out

def bridge(data):
    ''' Parses a BRIDGE packet, and returns a BRIDGEACK packet containing another client information, or empty headers if no client is in the wait state. 
    Parameters
    ----------
    data : packet
        The incoming packet to be parsed'''
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