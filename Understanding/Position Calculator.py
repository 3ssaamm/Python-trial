import numpy as np
from scipy.optimize import minimize
import random

# Set a random seed for reproducibility
np.random.seed(0)

# Define the objective function to minimize
# This function aims to find a point lander_position that is close to the target coordinates
def objective_function(lander_position, target_position):
    # Minimize the distance from the lander to the target position
    return np.linalg.norm(lander_position - target_position)

# Constraints for the minimization process
def constraint_distance_to_landing_site(lander_position, landing_site_position, expected_distance_lander_landing_site):
    return np.linalg.norm(lander_position - landing_site_position) - expected_distance_lander_landing_site

def constraint_distance_to_origin(lander_position, expected_distance_lander_origin):
    return np.linalg.norm(lander_position) - expected_distance_lander_origin

# Target position to approach (scaled 1:1000)
target_position = np.array([2000, 1600, -3500])

# Given values
landing_site_position = np.array([3211.5, 1075, -726])  # Landing site position coordinates
distance_landing_site_origin = 3463.587                # Distance from the landing site to the origin
distance_lander_origin = 4753.03                       # Expected distance from the lander to the origin
expected_distance_lander_landing_site = 3242.38        # Expected distance between the lander and the landing site

# Constraints dictionary
constraints = [
    {'type': 'eq', 'fun': constraint_distance_to_landing_site, 'args': (landing_site_position, expected_distance_lander_landing_site)},
    {'type': 'eq', 'fun': constraint_distance_to_origin, 'args': (distance_lander_origin,)}
]

# Perform the minimization
# Random initial guess for the lander's position
initial_guess = np.array([random.uniform(-5000, 5000) for _ in range(3)])

# Perform the minimization using the Sequential Least Squares Programming (SLSQP) method
result = minimize(objective_function, initial_guess, args=(target_position,),
                  method='SLSQP', constraints=constraints)

# Check if the minimization was successful and the constraints were satisfied
if result.success:
    optimized_lander_position = result.x
    print(f"The optimized lander's position: {optimized_lander_position}")
else:
    print("Optimization failed. Please check the constraints and initial guess.")
