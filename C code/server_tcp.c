#include <stdio.h>
#include <string.h>
#include <winsock2.h> // Windows Socket API library
#include <windows.h>  // Windows basic system header file

#pragma comment(lib, "ws2_32.lib")  // connecting to the ws2_32.lib in case not founding

int main() {
    WSADATA init_wsa; // defining wsa as the structure in winsock2 stores initialization information
    WSAStartup(0x0202, &init_wsa); // initializing the winsock with 2.2 edition

    SOCKET socket_listen, socket_comm; // define the socket variable for listening and communication
    struct sockaddr_in server_addr, client_addr; // define the sock address information in IPV4 for client and server
    int len_client_addr = sizeof(client_addr); // get length of client socket address


    char buffer[2048]; // define a buffer with max 2048 byte


    // starting a TCP socket
    // AF_INET: IPV4
    // Stream: Tcp
    socket_listen = socket(AF_INET, SOCK_STREAM, 0);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5050);
    server_addr.sin_addr.s_addr = INADDR_ANY; // listening to all IP

    // binding withe the socket
    bind(socket_listen, (struct sockaddr*)&server_addr, sizeof(server_addr));

    // listening under the port 5050 with allowing queue of 1 
    listen(socket_listen, 1);
    printf("Server starts on port 5050\n");

    // accept the connection after handshake established
    socket_comm = accept(socket_listen, (struct sockaddr*)&client_addr, &len_client_addr);
    printf("Client connected \n");

    // recieve message and print out
    memset(buffer, 0, sizeof(buffer));
    recv(socket_comm, buffer, sizeof(buffer), 0);
    printf("Client message: %s\n", buffer);

    // send back message
    send(socket_comm, buffer, strlen(buffer), 0);


    // closing all soackets and clean up
    closesocket(socket_comm);
    closesocket(socket_listen);
    WSACleanup();

    
    return 0;
}
