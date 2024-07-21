import socket
import time
import threading
import serial
import numpy as np



def parse_angles(x):
    ser = 'Current Euler Angles ['
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
                        print("Angles Sent to Orienteer:", angles)
                        if len(angles) == 3:
                            sendAngles(*angles)
                        else:
                            print("Received data does not contain three angles.")
                    except ValueError:
                        print("Error parsing angles from received data.")
                    time.sleep(0.01)
        except socket.error as e:
            print(f"Error receiving data: {e}")
            break


import random
options = [0,50,100]

# Function to fire thrusters
def fire_thrusters(sock, thrusters_magnitudes):
    def send_thrusters_data():
        global data_sent_count
        try:
            thrusters_magnitudes = [random.choice(options) for i in range(4)]
            thrusters_magnitudes_string = ";".join(map(str, thrusters_magnitudes))
            sock.sendall(thrusters_magnitudes_string.encode('utf-8'))
            print(f"Sent command to Unity: {thrusters_magnitudes_string}")
            data_sent_count += 1
            print("Thrusters Counter:", data_sent_count, "\n")
            thrusters_magnitudes[0] = round(thrusters_magnitudes[0], 2)
            print(f"Thrusters Magnitudes changed to: {thrusters_magnitudes}")
            timer = threading.Timer(0.5, send_thrusters_data)
            timer.start()
        except socket.error as e:
            print("Error sending data to server: {}".format(e))

    timer = threading.Timer(1.0, send_thrusters_data)
    timer.start()

thrusters_magnitudes = [0, 50, 0, 0]  # [A1, A2, B1, B2]%

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








class MarsEntryGuidance:
    """
    This class represents a simplified Mars entry guidance system inspired by Apollo and MSL approaches.
    """

    def __init__(self, mass, dt=0.1):
        self.mass = mass
        self.dt = dt

        # Constants
        self.G = 6.6743e-11  # Gravitational constant
        self.R_mars = 3389e3  # Mars radius
        self.max_bank_angle = np.pi / 6

        # Target point and tolerance
        self.target_x = 0
        self.target_y = 0
        self.target_z = 10000
        self.tolerance = 0.1

        # Gain schedule (example)
        self.K_downrange = 0.1
        self.K_heading = 0.05
        self.K_roll =1

        # Initial state (placeholder)
        self.state = None

    def set_initial_state(self, x, y, z, vx, vy, vz):
        """
        Sets the initial state of the spacecraft.
        """
        self.state = np.array([x, y, z, vx, vy, vz])

    def reference_bank_angle(self,  state, ):
        """Bank angle function for open loop guidance that simply returns
           the reference bank angle"""
        x, y, z, vx, vy, vz = state
        v= np.sqrt(vx**2+vy**2+vz**2)
        if v >= 3500:
            return np.deg2rad(75)
        elif v <= 1500:
            return np.deg2rad(50)
        else:
            return np.deg2rad(50 + (75-50)*(v-1500)/(3500-1500))
    def rho(self, z):
        """
        Returns the atmospheric density at a given altitude using the U.S. Standard Atmosphere (Mars) model.
        """
        # Replace with your preferred atmospheric model or interpolation method
        # Here's an example using the U.S. Standard Atmosphere (Mars) model:
        h = z + self.R_mars  # Convert altitude to geopotential altitude
        if h < 0:
            return 0.0  # No atmosphere below ground
        elif h <= 25000:
            # Use exponential profile for lower altitudes
            return 0.01225 * np.exp(-h / 6500)
        else:
            # Use constant density for higher altitudes
            return 0.001

    def C_l(self, mach, alpha):
        """
        Returns the lift coefficient based on Mach number and angle of attack.
        """
        # Replace with your chosen lift coefficient model based on Mach number and spacecraft geometry
        # Here's an example using a simplified linear model:
        return 0.8 * alpha - 0.2  # Adjust coefficients based on your model

    def C_d(self, mach):
        """
        Returns the drag coefficient based on Mach number.
        """
        # Replace with your chosen drag coefficient model based on Mach number and spacecraft geometry
        # Here's an example using a basic model:
        return 0.8  # Adjust coefficient based on your model
    def T(self, z):
        """
        Returns the atmospheric temperature at a given altitude using the U.S. Standard Atmosphere (Mars) model.
        """
        h = z + self.R_mars  # Convert altitude to geopotential altitude
        if h < 0:
            return 140  # Constant temperature below ground
        elif h <= 25000:
            # Use linear temperature profile for lower altitudes
            return 140 - 0.0028 * h / 1000  # Adjust coefficients based on actual model
        else:
            # Use constant temperature for higher altitudes
            return 110  # Adjust constant value according to actual model
    def A_ref(self):
        # ... (set a constant value or use a calculation based on your scenario) ...
        return 15.9  # Replace with the appropriate value

    def update_state(current_state, acceleration, time_step):
        """
        This function updates the spacecraft state based on acceleration and time step.

        Args:
            current_state: A numpy array representing the current state (x, y, z, vx, vy, vz).
            acceleration: A numpy array representing the acceleration (ax, ay, az).
            time_step: The time step between calculations (seconds).

        Returns:
            A numpy array representing the updated state (x, y, z, vx, vy, vz) at the next time step.
        """

        # Update position
        new_position = current_state[:3] + current_state[3:6] * time_step + 0.5 * acceleration[:3] * time_step**2

        # Update velocity
        new_velocity = current_state[3:6] + acceleration * time_step

        # Combine updated state
        new_state = np.concatenate((new_position, new_velocity))

        return new_state

    def dynamics_model(self, state, bank_angle):
        """
        Updates the state of the spacecraft based on the dynamics model.
        """
        x, y, z, vx, vy, vz = state

        # Compute forces
        v= np.sqrt(vx**2+vy**2+vz**2)
        gamma = np.arctan2(state[5], state[3])
        gravity = self.G * self.mass / (z + self.R_mars)**2
        mach = v / np.sqrt(gamma * 287 * self.T(z))  # Calculate Mach number based on temperature
        alpha = bank_angle  # Assume angle of attack equals bank angle
        C_d = self.C_d(mach)  # Use calculated drag coefficient
        drag = -0.5 * C_d * self.A_ref() * self.rho(z) * v**2 / v
        lift = 0.5 * self.C_l(mach, alpha) * self.A_ref ()* self.rho(z) * v**2 * np.cos(bank_angle)

        acc_x = drag * vx / v
        acc_y = drag * vy / v + lift * np.sin(bank_angle)
        acc_z = -gravity + drag * vz / v + lift * np.cos(bank_angle)
        acc = np.array([acc_x, acc_y, acc_z])
        # there are two methods to compute the new state make sure to use just one of them and comment the other
        # Compute new state using Runge-Kutta method:
        # k1 = acc * self.dt
        # k2 = self.dynamics_model(state + k1 / 2, bank_angle)[3:] * self.dt
        # k3 = self.dynamics_model(state + k2 / 2, bank_angle)[3:] * self.dt
        # k4 = self.dynamics_model(state + k3, bank_angle)[3:] * self.dt
        # new_state = state + (k1 + 2 * k2 + 2 * k3 + k4) / 6
        # another way to compute new state is by integration for the acc using the update state function:
        new_state=self.update_state(state,acc,self.dt)

        return new_state

    def predict_state(self, state, bank_angle):
        """
        Predicts the state of the spacecraft at the target point using the current bank angle.
        """
        predicted_state = state
        while predicted_state[2] < self.target_z:
            predicted_state = self.dynamics_model(predicted_state, bank_angle)
        return predicted_state

    def bank_angle_control(self, state, predicted_state):
        """
        Calculates and adjusts the bank angle based on the predicted state and error correction.
        """
        # Downrange error
        error_downrange = predicted_state[0] - self.target_x

       

        # Adaptive gain based on flight phase (example)
        if state[2] > -50e3:
            self.K_downrange = 0.2
        else:
            self.K_downrange = 0.1

        # Update bank angle with downrange and heading control
        bank_angle = bank_angle - self.K_downrange * error_downrange 

        # Limit bank angle
        bank_angle = np.clip(bank_angle, -self.max_bank_angle, self.max_bank_angle)

        return bank_angle
    def bank_angle_control2(self, state, predicted_state):
            """
            Calculates and adjusts the bank angle based on the predicted state and error correction.
            """
           
            # Target Range-to-go (the downrange distance remaining between the spacecraft's current position and the target landing point.)
            R = np.sqrt((self.target_x-state[0])**2 + (self.target_y-state[1])**2)


            # Flight path angle
            gamma = np.arctan2(state[5], state[3])
            # Lift-to-drag ratio
            L_D = 0.24

            # Predicted range-to-go
            R_p = np.sqrt(( predicted_state[0]-state[0])**2 + ( predicted_state[1]-state[1])**2)

            # Desired vertical component of lift-to-drag ratio
            L_D_v = L_D*np.sin(gamma)+self.K_downrange * (R_p - R) / L_D 



            # Bank angle from vertical component of lift-to-drag ratio
            bank_angle = np.arccos((L_D_v) / L_D) * self.K_roll

            # Limit bank angle
            bank_angle = np.clip(bank_angle, -self.max_bank_angle, self.max_bank_angle)

            return bank_angle
    def guide(self):
            """
            Executes the guidance loop to steer the spacecraft towards the target point.
            """
            if self.state is None:
                raise ValueError("Initial state not set!")

            bank_angle = self.reference_bank_angle(self.state)

            while self.state[2] < self.target_z:
               

                # Predict state at target
                predicted_state = self.predict_state(self.state, bank_angle)
                bank_angle = self.bank_angle_control2(self.state, predicted_state)
                print(f'{bank_angle}')
                self.state = self.dynamics_model(self.state, bank_angle)
                # if abs(self.predicted_state[0] - self.target_x) < self.tolerance and \
                # abs(self.predicted_state[2] - self.target_z) < self.tolerance:
                #     print(f'{bank_angle , self.state[2] }')
                    
                # else:
                    
                #     # Calculate and adjust bank angle
                #     bank_angle = self.bank_angle_control2(self.state, predicted_state)
                #     print(f'{bank_angle}')
                #     # Apply bank angle and update state
                #     self.state = self.dynamics_model(self.state, bank_angle)
                    

            # Check landing success
            if abs(self.state[0] - self.target_x) < self.tolerance and \
            abs(self.state[1] - self.target_y) < self.tolerance and \
            abs(self.state[2] - self.target_z) < self.tolerance:
                print("Successful landing!")
                print(f'{bank_angle}')
            else:
                print("Landing accuracy outside tolerance.")
                print(f'{bank_angle}')


# MNG= MarsEntryGuidance(mass=2200)
# MNG.set_initial_state(0.0, 0.0, 125e3, 4000.0, -1000.0, -250.0)
# MNG.guide()
# def test_guidance_algorithm(mars_guidance, initial_state, target_state, tolerance, max_iterations=1000):
#   """
#   This function tests the Mars entry guidance algorithm by simulating the descent process.

#   Args:
#       mars_guidance: An instance of your MarsEntryGuidance class.
#       initial_state: A numpy array representing the initial state of the spacecraft (x, y, z, vx, vy, vz).
#       target_state: A numpy array representing the target landing point (x, y, z).
#       tolerance: The maximum allowed error in each dimension for landing success (x, y, z).
#       max_iterations: The maximum number of iterations allowed for the simulation.

#   Returns:
#       A dictionary containing:
#           success: True if the spacecraft landed within tolerance, False otherwise.
#           iterations: The number of iterations it took to reach the target or reach the maximum.
#           final_state: The state of the spacecraft at the end of the simulation.
#   """
#   # Set initial state
#   mars_guidance.set_initial_state(*initial_state)

#   # Simulation loop
#   for iteration in range(max_iterations):
#     # Predict state at target point
#     predicted_state = mars_guidance.predict_state(mars_guidance.state, mars_guidance.reference_bank_angle(mars_guidance.state))

#     # Check landing success
#     landing_error = np.abs(predicted_state[:3] - target_state[:3])
#     if all(error <= tolerance for error in landing_error):
#       return {
#           "success": True,
#           "iterations": iteration + 1,
#           "final_state": mars_guidance.state
#       }

#     # Calculate and adjust bank angle
#     mars_guidance.bank_angle_control(mars_guidance.state, predicted_state)

#     # Update state
#     mars_guidance.state = mars_guidance.dynamics_model(mars_guidance.state, mars_guidance.bank_angle_control(mars_guidance.state, predicted_state))

#   # Reached maximum iterations without landing
# #   return {
# #       "success": False,
# #       "iterations": max_iterations,
# #       "final_state": mars_guidance.state
# #   }


# # Define initial state (replace with your desired values)
# initial_state = np.array([0.0, 0.0, 125e3, 4000.0, -1000.0, -250.0])  # x, y, z, vx, vy, vz (meters)

# # Justification for initial state:
# #  - x, y: We assume a zero initial lateral position (0 meters) relative to the target.
# #  - z: Starting at -125 km above the Martian surface is a typical entry altitude for missions.
# #  - vx, vy: A hypersonic entry velocity of 4000 m/s (around Mach 12) is realistic for interplanetary travel.
# #  - vz: A negative vz (-250 m/s) indicates a downward velocity component.

# # Define target landing point (replace with your desired values)
# target_state = np.array([0.0, 0.0, -10.0])  # x, y, z (meters)

# # Tolerance for landing accuracy (replace with your desired values)
# tolerance = np.array([100.0, 100.0, 5.0])  # x, y, z (meters)

# # Justification for tolerance:
# #  - x, y: A landing accuracy of 100 meters in the horizontal plane is achievable, but challenging.
# #  - z: A vertical tolerance of 5 meters is a demanding target for pinpoint landing.

# # Maximum iterations for the simulation
# max_iterations = 1000

# # Create an instance of your MarsEntryGuidance class
# mars_guidance = MarsEntryGuidance(mass=2200.0)  # Replace mass with your spacecraft mass

# # Test the guidance algorithm using the test function
# # test_guidance_algorithm(mars_guidance, initial_state, target_state, tolerance, max_iterations)

# # # Print the test results
# # print(f"Landing Success: {test_result['success']}")
# # print(f"Iterations: {test_result['iterations']}")
# # print(f"Final State:\n {test_result['final_state']}")



import pygame
import math
import numpy as np
import random

###TODO: 
# To make it more accurate we can make the gravity to the center of the planet not downwards so the orbiting effect can happen
slower= 1000

atmo_layering_number = 15

time_from_start = 0



# Define colors
WHITE = (255, 255, 255)
THRUSTER_EFFECT_COLOR = (255, 255, 0)  # Yellow color for visibility

# Constants
MARS_GRAVITY = -3.71  # m/s^2

## TODO: Should be affected by the oriantaion
AIR_RESISTANCE_COEFF = 3 # (adjustable for different air densities) 
LD_C = 10 # (adjustable)


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCALE = 200  # meters per pixel (adjust for visual representation)


# User input (replace with prompts and error handling)
initial_altitude = 120000.0  # meters

# TODO: Get the accurate velocities
# total vel = 5333 = sqrt(initial_horizontal_velocity^2 + initial_vertical_velocity^2)
initial_horizontal_velocity = 100.0  # m/s (positive to the right)
initial_vertical_velocity = -533.0  # m/s (negative for downward)
max_thrust = 100.0  # m/s^2
spacecraft_mass = 1025  # kg
fuel_mass = 100.0  # kg # Hard to calculate real number so this is going to be arbtirary number 
fuel_consumption_rate = 1.0  # kg/s per unit of thrust (adjustable for engine efficiency)


# Simulation variables
x_position = SCALE*100  # meters
y_position = initial_altitude  # meters (matches initial altitude)
x_velocity = initial_horizontal_velocity
y_velocity = initial_vertical_velocity
fuel_remaining = fuel_mass # Hard to calculate real number so this is going to be arbtirary number 
total_fuel_time = 300 * slower  # Hard to calculate real number so this is going to be arbtirary number 
thrust_x = 0.0  # m/s^2 (horizontal thrust)
thrust_y = 0.0  # m/s^2 (vertical thrust)
orientation_change = 0.0 # change in orientation per dt
random_wind_factor = 5.0 # how much the wind affects the orientation of the spacecraft

# Colors    
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (133, 40, 20)  # For crash landing
YELLOW = (255, 255, 0)  # For successful landing
GREY = (170, 170, 170) # For

# New global variable for spacecraft orientation (in degrees)
spacecraft_orientation = 0.0

(left_wing_up_thruster_power, left_wing_down_thruster_power, right_wing_up_thruster_power,
 right_wing_down_thruster_power, top_left_thruster_power, top_right_thruster_power , 
 bottom_left_thruster_power, bottom_right_thruster_power) = (0,0,0,0,0,0,0,0)

control_ori_st= 0.08
control_pos_st= 0.001


# Define colors for the thruster effects
THRUSTER_EFFECT_COLOR = (255, 255, 0)  # Yellow color for visibility

# Example usage:
# Assuming 'screen' is your Pygame display surface and 'spacecraft_position' is the current position of your spacecraft
thruster_powers = {
    'left_wing_up': left_wing_up_thruster_power,
    'left_wing_down': left_wing_down_thruster_power,
    'right_wing_up': right_wing_up_thruster_power,
    'right_wing_down': right_wing_down_thruster_power,
    'top_left': top_left_thruster_power,
    'top_right': top_right_thruster_power,
    'bottom_left': bottom_left_thruster_power,
    'bottom_right': bottom_right_thruster_power
}






# Constants for colors (you can adjust these)
BLACK = (0, 0, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
MARS_SURFACE_COLOR = (115, 55, 0)  # Rusty Mars surface color
ATMOSPHERE_COLOR = (255, 200, 180, 40)  # Semi-transparent white for atmosphere
alphas = [ (220/np.power(i+2,0.3)) for i in range(atmo_layering_number)]

def apply_thrust(dt):
    global x_velocity, y_velocity, fuel_remaining, spacecraft_orientation
    global left_wing_up_thruster_power, left_wing_down_thruster_power
    global right_wing_up_thruster_power, right_wing_down_thruster_power
    global top_left_thruster_power, top_right_thruster_power
    global bottom_left_thruster_power, bottom_right_thruster_power

    # Limit thrust based on fuel availability
    if fuel_remaining > 0:
        # Calculate the actual thrust force for each thruster based on the power level (0 to 100%) and max thrust capability
        left_wing_vertical_force = (left_wing_up_thruster_power - left_wing_down_thruster_power) / 100.0 * max_thrust
        right_wing_vertical_force = (right_wing_up_thruster_power - right_wing_down_thruster_power) / 100.0 * max_thrust
        top_horizontal_force = (top_right_thruster_power  - top_left_thruster_power) / 100.0 * max_thrust
        bottom_horizontal_force = (bottom_right_thruster_power - bottom_left_thruster_power) / 100.0 * max_thrust


        
        # Calculate the net force differences for rotation and movement
        net_vertical_force = right_wing_vertical_force + left_wing_vertical_force
        net_horizontal_force =  (top_horizontal_force + bottom_horizontal_force)
        
        # Update the spacecraft's orientation based on the net force differences
        rotation_rate = (right_wing_vertical_force - left_wing_vertical_force + bottom_horizontal_force - top_horizontal_force) * dt 
        spacecraft_orientation -= rotation_rate * control_ori_st

        if abs(spacecraft_orientation)>360:
            spacecraft_orientation -=  (spacecraft_orientation/abs(spacecraft_orientation))*360
        
        # Convert orientation to radians for trigonometric functions
        orientation_radians = math.radians(spacecraft_orientation)
        
        # Calculate the effective thrust components in the inertial frame based on the spacecraft's orientation
        effective_thrust_x = -math.cos(orientation_radians) * net_horizontal_force + math.sin(orientation_radians) * net_vertical_force
        effective_thrust_y = math.sin(orientation_radians) * net_horizontal_force + math.cos(orientation_radians) * net_vertical_force
        
        # Update velocities based on the effective thrust forces in the inertial frame
        x_velocity += effective_thrust_x * dt *control_pos_st
        y_velocity += (effective_thrust_y *control_pos_st + MARS_GRAVITY) * dt  # Including gravity in the vertical velocity update
        
        # Fuel consumption is based on the total thrust exerted by all thrusters
        total_thrust = (abs(left_wing_vertical_force) + abs(right_wing_vertical_force) + 
                        abs(top_horizontal_force) + abs(bottom_horizontal_force))
        fuel_remaining -= 1/total_fuel_time



def draw_spacecraft_info(screen, x, y, x_velocity, y_velocity, orientation, left_thruster, 
                         right_thruster, up_thruster, down_thruster, font_size=16, font_color=WHITE):
    """
    Draws text displaying the spacecraft's velocities, orientation, and thruster levels.

    Args:
        screen: The Pygame display surface.
        x: The x-coordinate of the spacecraft's center.
        y: The y-coordinate of the spacecraft's center.
        x_velocity: The spacecraft's x-axis velocity (m/s).
        y_velocity: The spacecraft's y-axis velocity (m/s).
        orientation: The spacecraft's current orientation (degrees).
        left_thruster: The power level of the left vertical thruster (%).
        right_thruster: The power level of the right vertical thruster (%).
        up_thruster: The power level of the up horizontal thruster (%).
        down_thruster: The power level of the down horizontal thruster (%).
        font_size: The size of the font used to display the text (default: 16).
        font_color: The color of the text (default: WHITE).
    """
    font = pygame.font.SysFont(None, font_size)

    # Format the text for velocity, orientation, and thruster levels
    x_velocity_text = f"X-Velocity: {x_velocity:.1f} m/s"
    y_velocity_text = f"Y-Velocity: {y_velocity:.1f} m/s"
    orientation_text = f"Orientation: {-orientation:.1f}°"
    left_thruster_text = f"Left Thrust: {left_thruster}%"
    right_thruster_text = f"Right Thrust: {right_thruster}%"
    up_thruster_text = f"Up Thrust: {up_thruster}%"
    down_thruster_text = f"Down Thrust: {down_thruster}%"

    # Render the text surfaces
    x_text_surface = font.render(x_velocity_text, True, font_color)
    y_text_surface = font.render(y_velocity_text, True, font_color)
    orientation_surface = font.render(orientation_text, True, font_color)
    left_thruster_surface = font.render(left_thruster_text, True, font_color)
    right_thruster_surface = font.render(right_thruster_text, True, font_color)
    up_thruster_surface = font.render(up_thruster_text, True, font_color)
    down_thruster_surface = font.render(down_thruster_text, True, font_color)

    # Get the text surface dimensions for positioning
    x_text_width, x_text_height = x_text_surface.get_size()
    y_text_width, y_text_height = y_text_surface.get_size()
    orientation_width, orientation_height = orientation_surface.get_size()
    left_thruster_width, left_thruster_height = left_thruster_surface.get_size()
    right_thruster_width, right_thruster_height = right_thruster_surface.get_size()
    up_thruster_width, up_thruster_height = up_thruster_surface.get_size()
    down_thruster_width, down_thruster_height = down_thruster_surface.get_size()

    # Place the text surfaces below the spacecraft with some offset
    text_x = x - max(x_text_width, y_text_width, orientation_width, left_thruster_width, 
                     right_thruster_width, up_thruster_width, down_thruster_width) // 2
    text_y = y + x_text_height + 20  # Position the text slightly below the spacecraft

    # Blit the text surfaces onto the screen
    screen.blit(x_text_surface, (text_x, text_y))
    screen.blit(y_text_surface, (text_x, text_y + y_text_height))
    screen.blit(orientation_surface, (text_x, text_y + 2 * y_text_height))
    screen.blit(left_thruster_surface, (text_x, text_y + 3 * y_text_height))
    screen.blit(right_thruster_surface, (text_x, text_y + 4 * y_text_height))
    screen.blit(up_thruster_surface, (text_x, text_y + 5 * y_text_height))
    screen.blit(down_thruster_surface, (text_x, text_y + 6 * y_text_height))



def handle_thrust_controls(keys_pressed):
    """
    Checks for keyboard clicks and updates thruster power levels based on user input.

    Args:
        keys_pressed: A dictionary containing the state of all pressed keys (True for pressed, False for not pressed).

    Modifies:
        Updates the global variables for the thruster power levels.
    """
    global max_thrust
    global left_wing_up_thruster_power, left_wing_down_thruster_power
    global right_wing_up_thruster_power, right_wing_down_thruster_power
    global top_left_thruster_power, top_right_thruster_power
    global bottom_left_thruster_power, bottom_right_thruster_power

    # Reset thruster powers to zero
    left_wing_up_thruster_power = 0.0
    left_wing_down_thruster_power = 0.0
    right_wing_up_thruster_power = 0.0
    right_wing_down_thruster_power = 0.0
    top_left_thruster_power = 0.0
    top_right_thruster_power = 0.0
    bottom_left_thruster_power = 0.0
    bottom_right_thruster_power = 0.0

    # Adjust these key codes based on your desired controls
    # Wing thrusters control vertical movement and orientation
    if keys_pressed[pygame.K_q]:  # 'Q' key for left wing up thruster
        left_wing_up_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_a]:  # 'A' key for left wing down thruster
        left_wing_down_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_e]:  # 'E' key for right wing up thruster
        right_wing_up_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_d]:  # 'D' key for right wing down thruster
        right_wing_down_thruster_power = 100.0  # Full power

    # Top and bottom thrusters control horizontal movement and orientation
    if keys_pressed[pygame.K_j]:  # 'J' key for top left thruster
        top_left_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_l]:  # 'L' key for top right thruster
        top_right_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_u]:  # 'U' key for bottom left thruster
        bottom_left_thruster_power = 100.0  # Full power
    if keys_pressed[pygame.K_o]:  # 'O' key for bottom right thruster
        bottom_right_thruster_power = 100.0  # Full power



def update_orientation(dt):
    global spacecraft_orientation
    global max_thrust
    global left_wing_up_thruster_power, left_wing_down_thruster_power
    global right_wing_up_thruster_power, right_wing_down_thruster_power
    global top_left_thruster_power, top_right_thruster_power
    global bottom_left_thruster_power, bottom_right_thruster_power

    # Calculate the net force differences for rotation
    net_vertical_force_difference = (right_wing_up_thruster_power - right_wing_down_thruster_power) - \
                                    (left_wing_up_thruster_power - left_wing_down_thruster_power)
    net_horizontal_force_difference = (bottom_right_thruster_power - bottom_left_thruster_power) - \
                                      (top_right_thruster_power - top_left_thruster_power)

    # Calculate the orientation change based on the net force differences
    # The multipliers can be adjusted to represent the sensitivity of the spacecraft's rotation
    orientation_change = (net_vertical_force_difference + net_horizontal_force_difference) * dt * 0.05  # Arbitrary value for rotation sensitivity

    # Update the spacecraft orientation based on the combined orientation changes
    spacecraft_orientation += orientation_change


def apply_random_wind_effect(c):
    """Add a small random change in the orintaion, 
    soon will also add it to the velocity distribution"""

    global orientation_change,spacecraft_orientation
    rotation = orientation_change
    if not c%10:
        rotation += (random.random()-0.5)*random_wind_factor

    spacecraft_orientation+=rotation




### NEW: in 3_1
def get_mars_atmospheric_density(altitude):
    """
    Calculates the atmospheric density on Mars at a given altitude.

    Args:
        altitude: Altitude in meters.

    Returns:
        Density in kg/m^3.
    """
    # Define the altitude ranges for the lower and upper atmosphere
    lower_atmosphere_altitude = 7000  # meters

    # Calculate temperature and pressure based on altitude
    if altitude <= lower_atmosphere_altitude:
        # Lower atmosphere (surface to 7,000 meters)
        temperature = -31 - 0.000998 * altitude
        pressure = 0.699 * np.exp(-0.00009 * altitude)
    else:
        # Upper atmosphere (above 7,000 meters)
        temperature = -23.4 - 0.00222 * altitude
        pressure = 0.699 * np.exp(-0.00009 * altitude)

    # Calculate density using the ideal gas law
    density = pressure / (0.1921 * (temperature + 273.1))

    return density




def apply_air_resistance_v2(dt):
    """
    Calculates and applies air resistance force to each component of the spacecraft's velocity.

    Args:
        dt: Timestep (seconds).
        density: The air density (kg/m^3). Defaults to 0.02 (approximate Martian surface density).
    """
    global y_velocity ,x_velocity,y_position

    density = get_mars_atmospheric_density(y_position)*3

    # Adjust drag coefficients based on Mach number (placeholder values)
    drag_coefficient_x = calculate_drag_coefficient(x_velocity / 240)  # Adjust for Mars speed of sound
    drag_coefficient_y = calculate_drag_coefficient(y_velocity / 240)

    # TODO: add bank angle
    # Calculate air resistance forces
    air_resistance_force_x = -0.5 * density * drag_coefficient_x * np.pi * (x_velocity**2) *AIR_RESISTANCE_COEFF 
    air_resistance_force_y = 0.5 * density * drag_coefficient_y * np.pi * (y_velocity**2) * AIR_RESISTANCE_COEFF # cos bank angle

    # Update velocity components
    x_velocity += air_resistance_force_x * dt / spacecraft_mass
    y_velocity += air_resistance_force_y * dt / spacecraft_mass

    return np.array([x_velocity, y_velocity])


def calculate_drag_coefficient(mach_number):
    """
    Placeholder function to calculate drag coefficient based on Mach number.
    Replace with your actual implementation.
    """
    if mach_number <= 1:
        return 1.0  # Drag coefficient for subsonic speeds
    else:
        return 0.5  # Simplified drag coefficient for supersonic speeds

def apply_gravity(dt):
    global y_velocity
    y_velocity += MARS_GRAVITY * dt





def update_position(dt):
    global x_position, y_position
    x_position += x_velocity * dt
    y_position += y_velocity * dt





def draw_stars(screen,amount=3):

        # Draw stars in the background
        for _ in range(amount):
            star_x = np.random.randint(0, screen.get_width())
            star_y = np.random.randint(0, screen.get_height())
            pygame.draw.circle(screen, WHITE, (star_x, star_y), 1)





def draw_environment(screen):
    global time_from_start, dt
    """
    Draws an enhanced Martian environment on the Pygame screen.

    Customize this function to create a visually appealing representation.
    Suggestions:
        - Use an image for the Martian surface (texture).
        - Add layers of atmosphere (semi-transparent) and texture.
        - Incorporate Martian features like craters and mountains.
    """
    screen.fill(BLACK)  # Fill the background with black
    time_from_start+=dt
    current_height = y_position

    draw_stars(screen,2)

    
    # Load the Mars surface texture (replace 'mars_texture.png' with your image file)
    mars_texture = pygame.image.load(r'under_dev\drawing_v0_3\docs\mars_texture.png').convert_alpha()
    mars_background = pygame.image.load(r'under_dev\drawing_v0_3\docs\mars_background.png').convert_alpha()
    mars_background = pygame.transform.scale(mars_background, (SCREEN_WIDTH,SCREEN_HEIGHT))
 
    # Create a copy of the texture with adjusted opacity (60%)
    textured_surface = mars_texture.copy()
    textured_surface.set_alpha(120)  # 60% opacity (255 * 0.6)
    

    # Draw a solid rectangle for the Martian ground color
    pygame.draw.rect(screen, MARS_SURFACE_COLOR, (0, screen.get_height() - 50, screen.get_width(), 50))

    screen.blit(textured_surface, ( 0,screen.get_height() - 50))
    screen.blit(mars_background, ( 0,0))
    # Display mission information (time from start and current height)
    font = pygame.font.Font(None, 24)
    info_text = f"Time: {time_from_start:.2f} s  |  Height: {current_height/1000:.3f} km"
    text_surface = font.render(info_text, True, GREY)
    screen.blit(text_surface, (10, 10))

    # Draw a scale (ruler) for pixels to meters
    scale_length_pixels = 100
    scale_length_meters = SCALE*scale_length_pixels/1000
    scale_start_x = 10
    scale_end_x = scale_start_x + scale_length_pixels
    pygame.draw.line(screen, WHITE, (scale_start_x, 30), (scale_end_x, 30), 2)
    font_small = pygame.font.Font(None, 20)
    scale_label = f"{scale_length_meters} km"
    label_surface = font_small.render(scale_label, True, GREY)
    screen.blit(label_surface, (scale_start_x, 35))


    ### COMMENTED TO REDUCE REQUIRED RESOURCES

    # # Draw layers of atmosphere 
    # for i in range(atmo_layering_number):
    #     atmosphere_color = ATMOSPHERE_COLOR
    #     atmosphere_rect = pygame.Rect(0, screen.get_height()-((i+1)*(SCREEN_HEIGHT)//atmo_layering_number)
    #                                   , screen.get_width(), screen.get_height()-((i*(SCREEN_HEIGHT)//atmo_layering_number)))
        


    #     atmosphere_surface = pygame.Surface(atmosphere_rect.size, pygame.SRCALPHA)


    #     atmosphere_surface.set_alpha(alphas[i])
    #     pygame.draw.rect(atmosphere_surface, atmosphere_color, atmosphere_rect)
    #     screen.blit(atmosphere_surface, (0, 0))
    

    
    # Draw the altitude scale (ruler) on the right side
    
    draw_ruler(screen)


def draw_ruler(screen):
    scale_x = screen.get_width() - 20
    scale_y_start = 20
    scale_y_end = screen.get_height() - 50
    pygame.draw.line(screen, GREY, (scale_x-50, scale_y_start), (scale_x-50, scale_y_end), 2)
    font_size = 18

    # Add labeled intervals to the scale
    font_small = pygame.font.Font(None, font_size)
    for i_pixel in range(50, SCREEN_HEIGHT-scale_y_start-30,50):
        # print(i_pixel)
        label = f"{i_pixel*SCALE//1000} km"
        label_surface = font_small.render(label, True, GREY)
        pygame.draw.line(screen, GREY,( (scale_x - 42), (scale_y_end - i_pixel+font_size//3)),
                         ( (scale_x - 50), (scale_y_end - i_pixel+font_size//3)) , 1)
        screen.blit(label_surface, ((scale_x - 40), (scale_y_end - i_pixel) ))
        





def rotate_point(cx, cy, x, y, angle):
    sin_angle = math.sin(angle)
    cos_angle = math.cos(angle)
    
    # Translate point to origin
    x -= cx
    y -= cy
    
    # Rotate point
    x_new = x * cos_angle - y * sin_angle
    y_new = x * sin_angle + y * cos_angle
    
    # Translate point back
    x_new += cx
    y_new += cy
    
    return x_new, y_new



def draw_spacecraft(screen, x, y, angle):
    # Define the spacecraft shape with more details
    points = [
        (x, y - 30),  # Tip of the spacecraft (nose)
        (x - 5, y - 10),  # Start of left wing
        (x - 15, y + 10),  # End of left wing
        (x - 5, y + 15),  # Left base rear
        (x + 5, y + 15),  # Right base rear
        (x + 15, y + 10),  # End of right wing
        (x + 5, y - 10),  # Start of right wing
    ]
    
    # Rotate each point around the spacecraft's center to get the correct orientation
    rotated_points = []
    for point in points:
        rotated_point = rotate_point(x, y, point[0], point[1], math.radians(angle))
        rotated_points.append(rotated_point)
    
    # Draw the main body of the spacecraft
    pygame.draw.polygon(screen, WHITE, rotated_points)

    # Draw the cockpit as a circle
    cockpit_center = rotate_point(x, y, x, y - 20, math.radians(angle))
    pygame.draw.circle(screen, (0, 255, 0), cockpit_center, 5)

    # Optionally, draw flames for the thrusters if they are active
    # This would be done in the draw_thrusters_effect function, using similar principles


def draw_thrusters_effect(screen, spacecraft_position, spacecraft_orientation, thruster_powers):
    orientation_radians = math.radians(spacecraft_orientation)
    effect_length = 0.35  # Base length of the thruster effect

    # Define the offsets and angles for each thruster from the spacecraft's center
    thruster_info = {
        'left_wing_up': {'offset': (-10, 5), 'angle': 90},
        'left_wing_down': {'offset': (-10, 5), 'angle': -90},
        'right_wing_up': {'offset': (10, 5), 'angle': 90},
        'right_wing_down': {'offset': (10, 5), 'angle': -90},
        'top_left': {'offset': (0, 15), 'angle': 180},
        'top_right': {'offset': (0, 15), 'angle': 0},
        'bottom_left': {'offset': (0, -22), 'angle': 180},
        'bottom_right': {'offset': (0, -22), 'angle': 0}
    }

    for thruster, power in thruster_powers.items():
        if power > 0:  # Draw the effect only if the thruster is active
            info = thruster_info[thruster]
            offset_x, offset_y = info['offset']
            angle_offset = info['angle']
            start_pos = (
                spacecraft_position[0] + offset_x,
                spacecraft_position[1] + offset_y
            )
            rotated_offset_x, rotated_offset_y = rotate_point(0, 0, offset_x, offset_y, orientation_radians)
            start_pos = (
                spacecraft_position[0] + rotated_offset_x,
                spacecraft_position[1] + rotated_offset_y
            )
            end_pos = (
                start_pos[0] + effect_length * power * math.cos(orientation_radians + math.radians(angle_offset)),
                start_pos[1] + effect_length * power * math.sin(orientation_radians + math.radians(angle_offset))
            )
            pygame.draw.line(screen, THRUSTER_EFFECT_COLOR, start_pos, end_pos, 2)
            # print("thrusting")