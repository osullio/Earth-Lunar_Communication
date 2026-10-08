#include <stdio.h>
#include <string.h>
#include <winsock2.h> // Windows Socket API library
#include <windows.h>  // Windows basic system header file

#pragma comment(lib, "ws2_32.lib")  // connecting to the ws2_32.lib in case not founding

int main() {

    WSADATA init_wsa; // defining wsa as the structure in winsock2 stores initialization information
    WSAStartup(0x0202, &init_wsa); // initializing the winsock with 2.2 edition

    SOCKET socket_comm; // define the socket variable for listening and communication
    struct sockaddr_in server_addr, client_addr; // define the sock address information in IPV4 for client and server
    int len_client_addr = sizeof(client_addr); // get length of client socket address

    char buffer[2048]; // define a buffer with max 2048 byte

    // starting a TCP socket
    // AF_INET: IPV4
    // Stream: Tcp
    socket_comm = socket(AF_INET, SOCK_STREAM, 0);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5050);
    server_addr.sin_addr.s_addr = inet_addr("192.168.0.171");  // connecting to server

    // connect to server
    connect(socket_comm, (struct sockaddr*)&server_addr, sizeof(server_addr));
    printf("Connect to server\n");

    // get an input
    printf("Enter message: ");
    fgets(buffer, sizeof(buffer), stdin);

    // send message
    send(socket_comm, buffer, strlen(buffer), 0);
    
    // receive the response
    memset(buffer, 0, sizeof(buffer));
    recv(socket_comm, buffer, sizeof(buffer), 0);
    printf("Server message: %s\n", buffer);
    

    // closing all soackets and clean up
    closesocket(socket_comm);
    WSACleanup();


    return 0;
}
