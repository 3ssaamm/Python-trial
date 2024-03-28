import socket
import time

# Server setup for receiving data from Unity
host, port = "127.0.0.1", 25002
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data_received_count = 0  # Counter to keep track of data received

# Client setup for sending data to Unity
unity_host, unity_port = "127.0.0.1", 25001

try:
    # Server binds and listens for incoming connections
    server.bind((host, port))
    server.listen(1)
    print("Server waiting for data from Unity...")

    while True:
        # Server accepts a connection
        connection, address = server.accept()
        with connection:
            # Server receives data from Unity
            data = connection.recv(1024).decode("utf-8")
            print("Server received data from Unity:", data)

            # Increment the counter and print the count
            data_received_count += 1
            print("Data count:", data_received_count)
            print()  # Prints an empty line

        # Client setup for sending data to Unity
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Attempt to connect to the Unity server
        try:
            client.connect((unity_host, unity_port))
            print("Client connected to Unity, ready to send thruster data...")
        except ConnectionRefusedError:
            print("Connection failed. Retrying...")
            time.sleep(1)  # Wait for 1 second before retrying
            continue

        # Client sends thruster data to Unity
        thruster_data = [
            "1.0",   # front_left
            "3.0",   # front_right
            "0.0",   # back_left
            "2.0"    # back_right
        ]
        command = "fire_thrusters," + ";".join(thruster_data)
        client.sendall(command.encode("UTF-8"))
        print("Client sent thruster data to Unity")

        # Close the client connection
        client.close()

        # Pause execution for 1 second
        time.sleep(1)

except Exception as e:
    print("An error occurred:", e)

finally:
    # Close the server socket
    server.close()
    print("Server socket closed.")
