import socket

# Define the fire_thrusters function
def fire_thrusters(sock, thruster_data):
    # Create the command string
    command = f"fire_thrusters,{thruster_data}"
    # Send the command to Unity
    sock.sendall(command.encode("UTF-8"))
    # Receive confirmation from Unity
    receivedData = sock.recv(1024).decode("UTF-8")
    print(f"Thrusters Fired: {receivedData}")

# Initialize connection
host, port = "127.0.0.1", 25001
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))

# Thruster data for Mars 2020 rover (example values)
# Format: thruster_name:magnitude,direction
thruster_data = {
    "front_left": "1.0,forward",
    "front_right": "1.0,forward",
    "back_left": "1.0,backward",
    "back_right": "1.0,backward"
}

# Convert thruster data to a string format
thruster_command = ';'.join([f"{key}:{value}" for key, value in thruster_data.items()])

# Fire thrusters with the specified command
fire_thrusters(sock, thruster_command)

# Close the socket connection
sock.close()
