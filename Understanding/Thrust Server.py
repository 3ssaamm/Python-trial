import socket

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
# Format: [magnitude, direction]
thruster_data = [
    "1.0,forward",  # front_left
    "1.0,forward",  # front_right
    "1.0,backward", # back_left
    "1.0,backward"  # back_right
]

# Fire thrusters with the specified command
fire_thrusters(sock, thruster_data)

# Close the socket connection
sock.close()
