import socket
import time
import threading
import serial

# Set up the serial connection (change your port name and baud rate as needed)
ser = serial.Serial("COM6", 9600, timeout=1)

# Initialize connection for receiving sensor data
receive_host, receive_port = "127.0.0.1", 25002
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_sock.bind((receive_host, receive_port))
receive_sock.listen(1)

# Initialize connection for sending thruster data
send_host, send_port = "127.0.0.1", 25001
send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_sock.connect((send_host, send_port))  # Connect to Unity before starting the thread for firing thrusters

# Print a message indicating the start of connection attempts
print("Attempting to connect to Unity...")

# Wait until the connection is established
while True:
    try:
        connection, address = receive_sock.accept()
        # Print a message indicating successful connection and break out of the loop
        print("Successfully connected to Unity.")
        break
    except socket.error as e:
        print(f"Trying again due to an error connecting: {e}")
        time.sleep(1)

data_received_count = 0  # Counter to keep track of data received
data_sent_count = 0  # Counter to keep track of data sent
last_data_received_time = time.time()  # Time of last data received

# Function to send angles over the serial connection
def sendAngles(angle1, angle2, angle3):
    # Format the angles into a single string separated by commas
    data = f"{angle1},{angle2},{angle3}\n"
    # Send the formatted string over the serial connection
    ser.write(data.encode('ascii'))

# Function to receive sensor data
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
                    
                    # Extract Euler angles from the received data
                    try:
                        angles = list(map(float, data.split(',')))
                        if len(angles) == 3:
                            sendAngles(*angles)
                        else:
                            print("Received data does not contain three angles.")
                    except ValueError:
                        print("Error parsing angles from received data.")
                    
                    # Pause execution for a short period of time to prevent network congestion and excessive CPU usage
                    time.sleep(0.1)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break

# Function to fire thrusters
def fire_thrusters(sock, thrusters_magnitudes):
    def send_thrusters_data():
        global data_sent_count
        try:
            # Convert the list of thruster magnitudes to a string
            thrusters_magnitudes_string = ";".join(map(str, thrusters_magnitudes))
            # Send the command to Unity
            sock.sendall(thrusters_magnitudes_string.encode('utf-8'))
            print(f"Sent command to Unity: {thrusters_magnitudes_string}")
            data_sent_count += 1
            print("Thrusters Counter:", data_sent_count, "\n")
            # Continuously increase the first element of the thrusters_magnitudes list by 0.01 every second (example)
            thrusters_magnitudes[0] += 0.01
            thrusters_magnitudes[0] = round(thrusters_magnitudes[0], 2)
            print(f"Thrusters Magnitudes changed to: {thrusters_magnitudes}")
            # Create a new timer to call the send_thrusters_data function again in 1 second
            timer = threading.Timer(1.0, send_thrusters_data)
            timer.start()
        except socket.error as e:
            print("Error sending data to server: {}".format(e))

    # Start the timer to call the send_thrusters_data function for the first time
    timer = threading.Timer(1.0, send_thrusters_data)
    timer.start()

# Thruster data for Mars 2020 rover (example values)
thrusters_magnitudes = [50, 50, 50, 50]  # [A1, A2, B1, B2]%

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
    receive_thread.join(timeout=3)    # Wait for the receive_sensor_data thread to finish running for a maximum of 3 seconds
    fire_thread.join(timeout=3)    # Wait for the fire_thrusters thread to finish running for a maximum of 3 seconds
    
    # Check if both threads have finished running
    if not receive_thread.is_alive() and not fire_thread.is_alive():
        break
    
    # Check if it has been more than 3 seconds since the last data was received
    if time.time() - last_data_received_time > 3:
        # If it has been more than 3 seconds, stop the fire_thrusters thread
        stop_event.set()
        fire_thread.join()
        print("Stopped firing thrusters due to lack of data from Unity.")
        break
