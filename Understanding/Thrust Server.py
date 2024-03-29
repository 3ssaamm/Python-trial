import socket
import time

# Initialize connection
host, port = "127.0.0.1", 25001
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))

# Define the fire_thrusters function
def fire_thrusters(sock, thruster_data):
    # Create the command string
    command = "fire_thrusters," + ";".join(thruster_data)
    # Send the command to Unity
    sock.sendall(command.encode("UTF-8"))
    # Receive confirmation from Unity
    receivedData = sock.recv(1024).decode("UTF-8")
    print(f"Thrusters Fired: {receivedData}")

# Thruster data for Mars 2020 rover (example values)
# Format: [magnitude]
thruster_data = [
    "1.0",   # front_left
    "3.0",   # front_right
    "0.0",   # back_left
    "2.0"    # back_right
]

try:
    while True:
        # Fire thrusters with the specified command
        fire_thrusters(sock, thruster_data)
        # Wait for 1 second before sending the next command
        time.sleep(1)
except KeyboardInterrupt:
    # Close the socket connection when interrupted
    print("Interrupted by user, closing socket.")
    sock.close()
