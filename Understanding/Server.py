import socket
import time

# Initialize connection
host, port = "127.0.0.1", 25001
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))

# Define the set_attitude function
def set_attitude(sock, pitch, yaw, roll):
    # Create the command string
    command = f"set_attitude,{pitch},{yaw},{roll}"
    # Send the command to Unity
    sock.sendall(command.encode("UTF-8"))
    # Receive confirmation from Unity
    receivedData = sock.recv(1024).decode("UTF-8")
    print(f"Attitude Set: {receivedData}")


# Initial attitude values
# pitch, yaw, roll
# 5alasna
attitude = [0, 0, 0]  

while True:
    # Sleep for a short period
    time.sleep(0.05) 
    
    # Modify attitude values as needed
    attitude[0] += 1  # Increment pitch
    attitude[1] += 1  # Increment yaw
    attitude[2] += 1  # Increment roll
    
    # Apply the attitude function
    # Unpack the list into function arguments
    set_attitude(sock, *attitude)  
