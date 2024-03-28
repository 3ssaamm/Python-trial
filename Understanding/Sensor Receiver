import socket
import time

host, port = "0.0.0.0", 25002

# SOCK_STREAM means TCP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Bind the socket to the host and port
    server.bind((host, port))
    # Listen for incoming connections
    server.listen(1)
    print("Waiting for data from Unity...")

    while True:
        # Accept a connection
        connection, address = server.accept()

        with connection:
            # Receive the data from Unity
            data = connection.recv(1024).decode("utf-8")
            print("Received data from Unity:", data)

        # Pause execution for 2 seconds
        time.sleep(2)

finally:
    # Close the socket
    server.close()