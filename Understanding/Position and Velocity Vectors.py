import numpy as np

# Constants for unit conversion
MILES_TO_METERS = 1609.34
MPH_TO_METERS_PER_SEC = 0.44704
KM_TO_METERS = 1000

# Constants for Mars gravity
GRAVITY_MARS_CONSTANT = 3.71  # m/s² at the surface
RADIUS_MARS_KM = 3389.5  # km

# Given data
initial_coords_km = (2307.674, 1762.081, -3763.111)  # Initial coordinates of Point 1 in km
initial_coords_meters = np.array(initial_coords_km) * KM_TO_METERS
landing_spot_km = [3211.5, 1075, -726]  # Final landing spot coordinates in km
landing_spot_meters = np.array(landing_spot_km) * KM_TO_METERS

distances_miles = [2014.72, 1909.70, 395.24, 212.93, 48.70, 13.20, 9.21, 6.53, 2.69, 2.32, 1.4, 0.079411, 0.079237]  # Distance to the landing spot
altitudes_miles = [847.26, 781.63, 81.40, 35.22, 10.04, 8.54, 7.42, 6.05, 2.66, 2.29, 1.36, 0.013725, 0.012468]  # Altitude above Martian surface
velocities_mph = [10585.42, 10678.59, 11931.65, 11988.77, 2465.25, 1068.26, 945.35, 363.01, 200.56, 194.76, 182.36, 3.71, 1.68]  # Velocities in mph
times_str = ["15:28", "14:53", "06:49", "05:54", "04:29", "03:03", "02:46", "02:25", "01:25", "01:18", "01:00", "00:18", "00:16"]  # Time to touch down "min:sec"

# Convert distances, altitudes, and velocities to meters and meters per second
distances_meters = np.array(distances_miles) * MILES_TO_METERS
altitudes_meters = np.array(altitudes_miles) * MILES_TO_METERS
velocities_mps = np.array(velocities_mph) * MPH_TO_METERS_PER_SEC

# Function to convert time string to seconds
def time_str_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(":"))
    return minutes * 60 + seconds

# Convert times to seconds
times_seconds = [time_str_to_seconds(t) for t in times_str]

# Initial velocity vector (provided)
initial_velocity_vector = np.array([2900, 520, 3703])

# Function to calculate acceleration due to gravity on Mars as a function of altitude
def mars_gravity(altitude_meters):
    radius_mars_meters = RADIUS_MARS_KM * KM_TO_METERS
    distance_from_center = radius_mars_meters + altitude_meters
    return GRAVITY_MARS_CONSTANT * (radius_mars_meters / distance_from_center) ** 2

# Initialize position vectors with the initial coordinates
position_vectors = [initial_coords_meters]

# Calculate the position vectors and velocity vectors iteratively
velocity_vectors = [initial_velocity_vector]  # Initialize velocity vector
for i in range(len(distances_meters)):
    previous_position = position_vectors[-1]
    previous_velocity = velocity_vectors[-1]

    # Calculate the change in altitude for this step
    altitude_change = altitudes_meters[i] - previous_position[2]

    # Calculate the acceleration due to gravity at this altitude
    gravity = mars_gravity(altitudes_meters[i])

    # Calculate the time difference
    time_difference = times_seconds[i + 1] - times_seconds[i] if i < len(times_seconds) - 1 else 0

    # Use provided velocity as a reference, adjusting for gravity
    if i < len(velocities_mps) - 1:
        # Calculate the horizontal component of the provided velocity
        provided_velocity_horizontal = np.array([velocities_mps[i], velocities_mps[i]])  # Adjust this line
        # Calculate the direction vector for the horizontal movement
        direction = (landing_spot_meters[:2] - previous_position[:2]) / np.linalg.norm(landing_spot_meters[:2] - previous_position[:2])

        # Adjust the provided velocity for gravity
        provided_velocity_adjusted = np.array([provided_velocity_horizontal[0], provided_velocity_horizontal[1], velocities_mps[i] + gravity * time_difference])

        # Update the velocity vector
        velocity_vector = provided_velocity_adjusted
        velocity_vectors.append(velocity_vector)

    else:
        # For the last step, use the previous velocity
        velocity_vector = previous_velocity
        velocity_vectors.append(velocity_vector)

    # Update the position vector
    position_vector = previous_position + velocity_vector * time_difference
    position_vector[2] = altitudes_meters[i]  # Update altitude to the provided value
    position_vectors.append(position_vector)

# Ensure the final position is exactly the landing spot
position_vectors[-1] = landing_spot_meters

# Calculate the resultant position vectors (magnitudes)
resultant_positions = [np.linalg.norm(pos) for pos in position_vectors]

# Calculate the resultant velocity vectors (magnitudes)
resultant_velocities = [np.linalg.norm(vel) for vel in velocity_vectors]

# Convert velocities_mps to a list and append a dummy value for the last entry
velocities_mps = list(velocities_mps)
velocities_mps.append(0.0)

# Output the results with times, position vectors, and resultant magnitudes
print(f"{'Time to surface':<15} | {'Position vector':<50} | {'Resultant position (m)':<20} | {'Velocity vector':<50} | {'Resultant velocity (m/s)':<20} | {'Provided velocity (m/s)':<20}")
print("-"*195)
for i, (pos, res_pos, time_str, vel, res_vel, prov_vel) in enumerate(zip(position_vectors, resultant_positions, times_str, velocity_vectors + [None], resultant_velocities + [None], velocities_mps)):
    pos_str = f"[{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}]"
    if vel is not None:
        vel_str = f"[{vel[0]:.2f}, {vel[1]:.2f}, {vel[2]:.2f}]"
        res_vel_str = f"{res_vel:.2f}"
        prov_vel_str = f"{prov_vel:.2f}"
    else:
        vel_str = f"{'N/A':<50}"
        res_vel_str = "N/A"
        prov_vel_str = "N/A"
    print(f"{time_str:<15} | {pos_str:<50} | {res_pos:<20.2f} | {vel_str:<50} | {res_vel_str:<20} | {prov_vel_str:<20}")