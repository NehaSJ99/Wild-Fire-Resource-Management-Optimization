import pandas as pd
import numpy as np
from scipy.spatial import distance

# Load CSV data
df = pd.read_csv('/content/resources_output.csv')

# Assign priority levels
priority_map = {
    "Critical Day 1": 4,
    "Critical Day 2": 3,
    "At Risk Day 3": 2,
    "Safe Zone": 1
}

df["priority"] = df["fire_zone"].map(priority_map)

# Identify zones by priority
safe_zones = df[df["priority"] == 1]
at_risk_zones = df[df["priority"] == 2]
critical_zones_1 = df[df["priority"] == 4]
critical_zones_2 = df[df["priority"] == 3]

# Function to calculate nearest higher-priority zone
def find_nearest_zone(source_row, target_zones):
    if target_zones.empty:
        return None
    source_coords = (source_row["latitude"], source_row["longitude"])
    target_coords = target_zones[["latitude", "longitude"]].values
    distances = [distance.euclidean(source_coords, (t[0], t[1])) for t in target_coords]
    nearest_index = np.argmin(distances)
    return target_zones.iloc[nearest_index]

# Move resources from Safe Zones to Critical Day 1 (40%)
for idx, row in safe_zones.iterrows():
    nearest_critical = find_nearest_zone(row, critical_zones_1)
    if nearest_critical is not None:
        move_fraction = 0.4  # Move 40% of resources
        print(f"Move {int(row['firefighter_capacity'] * move_fraction)} firefighters and {int(row['water_tank_capacity'] * move_fraction)}L water from {row['county_name']} (Safe Zone) to {nearest_critical['county_name']} (Critical Day 1)")

# Move resources from At Risk Day 3 to Critical Day 2 (20%)
for idx, row in at_risk_zones.iterrows():
    nearest_critical_2 = find_nearest_zone(row, critical_zones_2)
    if nearest_critical_2 is not None:
        move_fraction = 0.2  # Move 20% of resources
        print(f"Move {int(row['firefighter_capacity'] * move_fraction)} firefighters and {int(row['water_tank_capacity'] * move_fraction)}L water from {row['county_name']} (At Risk Day 3) to {nearest_critical_2['county_name']} (Critical Day 2)")
