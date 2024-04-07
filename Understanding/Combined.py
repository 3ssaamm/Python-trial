import socket
import time
import threading

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
        # Print a message indicating successful connection and break out of the loop
        #print("Successfully connected to Unity.")
        break
    except socket.error as e:
        print(f"Trying again due to an error connecting: {e}")
        time.sleep(1)


data_received_count = 0  # Counter to keep track of data received
last_data_received_time = time.time()  # Time of last data received

# Define the receive_sensor_data function
def receive_sensor_data(sock, stop_event):
    global data_received_count
    global last_data_received_time
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
                    # Update the time of last data received
                    last_data_received_time = time.time()
                    # Pause execution for a short period of time to prevent network congestion and excessive CPU usage
                    time.sleep(0.01)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break

# Define the fire_thrusters function
def fire_thrusters(sock, thrusters_magnitudes):
    def send_thrusters_data():
        try:
            # Convert the list of thruster magnitudes to a string
            thrusters_magnitudes_string = ";".join(map(str, thrusters_magnitudes))
            # Send the command to Unity
            sock.sendall(thrusters_magnitudes_string.encode('utf-8'))
            print(f"Sent command to Unity: {thrusters_magnitudes_string}")
            # Continuously increase the first element of the thrusters_magnitudes list by 0.01 every second, (Example)
            thrusters_magnitudes[0] += 0.01
            thrusters_magnitudes[0] = round(thrusters_magnitudes[0], 2)
            print(f"Thrusters Magnitudes cahnged to: {thrusters_magnitudes}")
            # Create a new timer to call the send_thrusters_data function again in 1 second
            timer = threading.Timer(1.0, send_thrusters_data)
            timer.start()
        except socket.error as e:
            print("Error sending data to server: {}".format(e))

    # Start the timer to call the send_thrusters_data function for the first time
    timer = threading.Timer(1.0, send_thrusters_data)
    timer.start()

# Thruster data for Mars 2020 rover (example values)
thrusters_magnitudes = [100, 100, 100, 100]  # [A1, A2, B1, B2]%

# Create a threading event to signal when the receive_sensor_data thread should stop running
stop_event = threading.Event()

# Start the thread for receiving sensor data
receive_thread = threading.Thread(target=receive_sensor_data, args=(receive_sock, stop_event))
receive_thread.start()

# Start the thread for firing thrusters
fire_thread = threading.Thread(target=fire_thrusters, args=(send_sock, thrusters_magnitudes))
fire_thread.start()

# Join threads to the main thread
while True:
    receive_thread.join()    # Wait for the threads to finish running
    fire_thread.join()    # Wait for the threads to finish running
