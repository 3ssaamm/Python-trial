import socket
import threading
import time

# Initialize connection for sending thruster data
send_host, send_port = "127.0.0.1", 25001
send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Initialize connection for receiving sensor data
receive_host, receive_port = "127.0.0.1", 25002
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_sock.bind((receive_host, receive_port))
receive_sock.listen(1)

# Print a message indicating the start of connection attempts
print("Attempting to connect to Unity...")

# Wait until the connection is established
while True:
    try:
        send_sock.connect((send_host, send_port))
        receive_conn, receive_addr = receive_sock.accept()
        # Print a message indicating successful connection and break out of the loop
        print("Successfully connected to Unity.")
        break
    except socket.error as e:
        print(f"Error connecting: {e}")
        time.sleep(1)

# Define the receive_sensor_data function
def receive_sensor_data(sock):
    while True:
        try:
            # Receive the data from Unity
            data = sock.recv(1024).decode("utf-8")
            if not data:
                # If no data is received, break out of the loop
                break
            print("Received data from Unity:", data)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break

# Define the fire_thrusters function
def fire_thrusters(sock, thrusters_magnitudes):
    timeout = 5  # Set a timeout of 5 seconds
    start_time = time.time()
    while True:
        try:
            # Send the command to Unity
            sock.sendall(thrusters_magnitudes.encode('utf-8'))
            break
        except socket.error as e:
            print("Error sending data to server: {}".format(e))
            time.sleep(1)
        if time.time() - start_time > timeout:
            break

# Thruster data for Mars 2020 rover (example values)
thrusters_magnitudes = "0.20;0.25;0.25;0.25"  # "A1;A2;B1;B2"

# Create a thread for receiving sensor data
receive_thread = threading.Thread(target=receive_sensor_data, args=(receive_conn,))
receive_thread.start()

# Fire the thrusters
fire_thrusters(send_sock, thrusters_magnitudes)

# Join the receive thread to the main thread
receive_thread.join()

# Print a message indicating the end of the program
print("Program ended.")

# Close the sockets
send_sock.close()
receive_sock.close()
