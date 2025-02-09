import pandas as pd
import numpy as np
import json
from scipy.spatial import distance

# Load CSV data
df = pd.read_csv("resources_output.csv")

priority_map = {
    "Critical Day 1": 4,
    "Critical Day 2": 3,
    "At Risk Day 3": 2,
    "Safe Zone": 1
}

df["priority"] = df["fire_zone"].map(priority_map)

safe_zones = df[df["priority"] == 1]
at_risk_zones = df[df["priority"] == 2]
critical_zones_1 = df[df["priority"] == 4]
critical_zones_2 = df[df["priority"] == 3]

def find_nearest_zone(source_row, target_zones):
    if target_zones.empty:
        return None
    source_coords = (source_row["latitude"], source_row["longitude"])
    target_coords = target_zones[["latitude", "longitude"]].values
    distances = [distance.euclidean(source_coords, (t[0], t[1])) for t in target_coords]
    nearest_index = np.argmin(distances)
    return target_zones.iloc[nearest_index]

results = []

# Move resources from Safe Zones to Critical Day 1 (40%)
for idx, row in safe_zones.iterrows():
    nearest_critical = find_nearest_zone(row, critical_zones_1)
    if nearest_critical is not None:
        move_fraction = 0.4
        results.append({
            "from": row['county_name'],
            "to": nearest_critical['county_name'],
            "firefighters": int(row['firefighter_capacity'] * move_fraction),
            "water": int(row['water_tank_capacity'] * move_fraction),
            "from_zone": "Safe Zone",
            "to_zone": "Critical Day 1"
        })

# Move resources from At Risk Day 3 to Critical Day 2 (20%)
for idx, row in at_risk_zones.iterrows():
    nearest_critical_2 = find_nearest_zone(row, critical_zones_2)
    if nearest_critical_2 is not None:
        move_fraction = 0.2
        results.append({
            "from": row['county_name'],
            "to": nearest_critical_2['county_name'],
            "firefighters": int(row['firefighter_capacity'] * move_fraction),
            "water": int(row['water_tank_capacity'] * move_fraction),
            "from_zone": "At Risk Day 3",
            "to_zone": "Critical Day 2"
        })

# Print JSON result for Flask to capture
print(json.dumps(results))
