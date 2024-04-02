# hybridChat

GOALS:
* Learn how to build simple networked applications in Python 3.12.0
    - Built initially over TCP
    - Later developed over UDP
        - NOTE: Obviously UDP doesn't really make sense for a chat application due to the unreliability and lack of order, but this was meant as a learning experience. In the UDP implementation, I still made use of ACKs to confirm communications. This could have been implemented much more simply, but I wanted the user experience to be relatively consistent regardless of the server mode.

DESIGN:
* This project relies on a server application and client application. The clients communicate with the server to register themselves, and to bridge to other clients. Once a chat connection is established, the clients communicate independently of the server in P2P communication, making this a hybrid model network application.
    - SERVER:
        - In TCP/default mode, waits for a client to connect, and receives one input from the client and disconnects, making this is a non-persistent TCP connection.
        - In UDP mode, the server waits to receive a packet from a client.
        - The Server accepts PROBE, REGISTER, BRIDGE, CHAT, and QUIT packets:
            - PROBE packets are sent from the client on launch, and are used to determine if the server is being run in TCP mode or UDP mode. This allows the client to connect without needing to know what mode the server is ran in.
            - REGISTER packets contain client information including client ID, client IP, and client Port. This information is stored in the server for later use. Returns a REGACK, or REGNACK if ID is already in use.
            - BRIDGE packets just containt the client ID, and are used to indicate a client is ready to chat. The server either returns the full information of another client who is available for a connection, or returns a packet with empty header values.
            - CHAT packets contain the client IDs of two users in a chat, this indicates to the server to remove them from the registry.
            - QUIT packets contain the client ID and indicates a user has left, this indicates to the server to remove them from registry.
        - Added a simple mechanism to defend against DoS attacks. Server keeps a log of number of connections or packets from an IP. If that count exceeds 10 before starting a chat, that IP's packets aren't processed (udp) or their connection is immediately closed (tcp).
    - CLIENT:
        - On startup, client probes the server to determine if it should be ran in TCP or UDP mode.
        - When the client runs the /bridge command, it will receive either a packet with empty headers or a packet containing another user's information:
            - If it receives an empty packet, the client will enter a wait state. In TCP mode, this client is acting as a server as it waits to accept a connection from another client. In UDP mode, it is simply waiting to recieve a packet.
            - If it receives a packet with information, the client may then connect using the /chat command to connect to a client in the wait state and begin chatting.
        - While chatting, each user will send CHAT packets (different than the CHAT packets for the server) which contain the message. After sending a message, the application blocks until a message is received. Each packet is limited to 1024 bytes.

HOW TO USE:
1. Run server with command: `python server.py --port=<port of choice> <-u>`
    - the -u or --udp flag tells the server to be ran in UDP mode
2. Run a client with command: `python client.py --id="<id of choice>" --port=<port of choice> --server="<address of server with IP:PORT>"`
    - After connecting, Run `/register`, `/bridge` in order
3. Run another client with the same command, but with different ID and Port (if being ran on the same IP)
    - After connecting, Run `/register`, `/bridge`, `/chat` in order
* Can quit with `/quit` or ctrl-c at any time (unless bugged)

TO DO:
* Write test suite
