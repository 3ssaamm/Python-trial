import socket
import time
import threading
import serial

def parse_angles(x):
    ser = 'CurrentEulerAngles ['
    angs = x[x.find(ser)+len(ser):-1]
    angles = [int(float(ang)) for ang in angs.split(',')]
    return angles

# Set up the serial connection (change your port name and baud rate as needed)
for i in range(3):
    try:
        ser = serial.Serial("COM6", 9600, timeout=1)
        print("Serial connection established.")
        break
    except serial.SerialException as e:
        print(f"Failed to connect to serial port: {e}")
        time.sleep(1)

# Initialize connection for receiving sensor data
receive_host, receive_port = "127.0.0.1", 25002
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receive_sock.bind((receive_host, receive_port))
receive_sock.listen(1)

# Initialize connection for sending thruster data
send_host, send_port = "127.0.0.1", 25001
send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Print a message indicating the start of connection attempts
print("Attempting to connect to Unity...")

# Retry logic for connecting to Unity
for i in range(10):
    try:
        send_sock.connect((send_host, send_port))
        print("Successfully connected to Unity.")
        break
    except socket.error as e:
        print(f"Failed to connect to Unity on attempt {i + 1}: {e}")
        time.sleep(1)
else:
    print("Failed to connect to Unity after 3 attempts. Exiting.")
    exit(1)

# Wait until the connection is established
while True:
    try:
        connection, address = receive_sock.accept()
        print("Successfully connected to Unity for receiving data.")
        break
    except socket.error as e:
        print(f"Trying again due to an error connecting: {e}")
        time.sleep(1)

data_received_count = 0  # Counter to keep track of data received
data_sent_count = 0  # Counter to keep track of data sent
last_data_received_time = time.time()  # Time of last data received

# Function to send angles over the serial connection
def sendAngles(angle1, angle2, angle3):
    data = f"{angle1},{angle2},{angle3}\n"
    ser.write(data.encode('ascii'))

# Function to receive sensor data
def receive_sensor_data(sock, stop_event):
    global data_received_count
    global last_data_received_time
    while not stop_event.is_set():
        try:
            connection, address = sock.accept()
            with connection:
                while True:
                    data = connection.recv(1024).decode("utf-8")
                    if not data:
                        break
                    print("Received data from Unity:", data)
                    data_received_count += 1
                    print("Counter:", data_received_count, "\n")
                    last_data_received_time = time.time()
                    try:
                        angles = parse_angles(data)
                        print("angles to send:", angles)
                        if len(angles) == 3:
                            sendAngles(*angles)
                        else:
                            print("Received data does not contain three angles.")
                    except ValueError:
                        print("Error parsing angles from received data.")
                    time.sleep(0.1)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break

# Function to fire thrusters
def fire_thrusters(sock, thrusters_magnitudes):
    def send_thrusters_data():
        global data_sent_count
        try:
            thrusters_magnitudes_string = ";".join(map(str, thrusters_magnitudes))
            sock.sendall(thrusters_magnitudes_string.encode('utf-8'))
            print(f"Sent command to Unity: {thrusters_magnitudes_string}")
            data_sent_count += 1
            print("Thrusters Counter:", data_sent_count, "\n")
            thrusters_magnitudes[0] += 0.01
            thrusters_magnitudes[0] = round(thrusters_magnitudes[0], 2)
            print(f"Thrusters Magnitudes changed to: {thrusters_magnitudes}")
            timer = threading.Timer(1.0, send_thrusters_data)
            timer.start()
        except socket.error as e:
            print("Error sending data to server: {}".format(e))

    timer = threading.Timer(1.0, send_thrusters_data)
    timer.start()

thrusters_magnitudes = [0, 0, 0, 0]  # [A1, A2, B1, B2]%

stop_event = threading.Event()

receive_thread = threading.Thread(target=receive_sensor_data, args=(receive_sock, stop_event))
receive_thread.start()

fire_thread = threading.Thread(target=fire_thrusters, args=(send_sock, thrusters_magnitudes))
fire_thread.start()

while True:
    receive_thread.join(timeout=3)
    fire_thread.join(timeout=3)
    if not receive_thread.is_alive() and not fire_thread.is_alive():
        break
    if time.time() - last_data_received_time > 3:
        stop_event.set()
        fire_thread.join()
        print("Stopped firing thrusters due to lack of data from Unity.")
        break
