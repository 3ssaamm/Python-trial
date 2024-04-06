import socket
import threading

# Create a TCP socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as e:
    print("Error creating socket: {}".format(e))
    exit()

# Connect to the server
try:
    sock.connect(('127.0.0.1', 25001))
except socket.error as e:
    print("Error connecting to server: {}".format(e))
    exit()

# Create a thread to send data to the server
def send_data():
    while True:
        # Get the thruster magnitudes from the user
        thruster_magnitudes = "0.25;0.25;0.25;0.25"

        # Send the data to the server
        try:
            sock.sendall(thruster_magnitudes.encode('utf-8'))
        except socket.error as e:
            print("Error sending data to server: {}".format(e))
            exit()

# Start the thread
threading.Thread(target=send_data).start()

# Keep the main thread running
while True:
    pass
