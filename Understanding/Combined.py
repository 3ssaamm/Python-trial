import socket
import time
import threading

# Initialize connection for sending thruster data
send_host, send_port = "127.0.0.1", 25001
send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Wait until the connection is established
while True:
    try:
        send_sock.connect((send_host, send_port))
        break
    except socket.error as e:
        print(f"Error connecting: {e}")
        time.sleep(1)

# Initialize connection for receiving sensor data
receive_host, receive_port = "127.0.0.1", 25002
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_sock.bind((receive_host, receive_port))
receive_sock.listen(1)

data_received_count = 0  # Counter to keep track of data received

# Define the fire_thrusters function
def fire_thrusters(sock, thruster_data):
    while True:
        # Create the command string
        command = "fire_thrusters," + ";".join(thruster_data)
        # Send the command to Unity
        try:
            sock.sendall(command.encode("UTF-8"))
            print("Thrustres fired successfully!")
        except socket.error as e:
            print(f"Error sending data: {e}")
            break
        # Wait for a short period of time to prevent network congestion and excessive CPU usage
        time.sleep(1)

# Define the receive_sensor_data function
def receive_sensor_data(sock, stop_event):
    global data_received_count
    while not stop_event.is_set():
        try:
            # Accept the connection from Unity
            connection, address = sock.accept()
            with connection:
                while True:
                    # Receive the data from Unity
                    data = connection.recv(1024).decode("utf-8")
                    if not data:
                        # If no data is received, break out of the inner loop
                        break
                    print("Received data from Unity:", data)
                    # Increment the counter and print the count
                    data_received_count += 1
                    print("Counter:", data_received_count, "\n")
                    # Pause execution for a short period of time to prevent network congestion and excessive CPU usage
                    time.sleep(0.01)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break

# Thruster data for Mars 2020 rover (example values)
thruster_data = [
    "1.0",   # front_left
    "3.0",   # front_right
    "0.0",   # back_left
    "2.0"    # back_right
]

# Create a threading event to signal when the receive_sensor_data thread should stop running
stop_event = threading.Event()

# Start the thread for receiving sensor data
receive_thread = threading.Thread(target=receive_sensor_data, args=(receive_sock, stop_event))
receive_thread.start()

# Start the thread for firing thrusters
fire_thread = threading.Thread(target=fire_thrusters, args=(send_sock, thruster_data))
fire_thread.start()

# Join threads to the main thread
try:
    receive_thread.join()
    fire_thread.join()
finally:
    # Close the sockets
    send_sock.close()
    receive_sock.close()
