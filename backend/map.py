import folium
import requests, os
from folium.plugins import MarkerCluster

# Fire location (latitude, longitude)
fire_location = (34.052235, -118.243683)  # Example: Los Angeles wildfire

# Fire stations nearby (latitude, longitude)
fire_stations = [
    (34.061400, -118.301380),  # Fire Station 1
    (34.042000, -118.250000),  # Fire Station 2
    (34.080000, -118.290000)   # Fire Station 3
]

def get_fastest_route(origin, destination):
    """Gets the fastest route using OSRM public API."""
    try:
        # OSRM requires coordinates in (longitude, latitude) order
        origin_str = f"{origin[1]},{origin[0]}"
        dest_str = f"{destination[1]},{destination[0]}"
        
        # Make request to OSRM API
        url = f"http://router.project-osrm.org/route/v1/driving/{origin_str};{dest_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if response.status_code == 200 and data["code"] == "Ok":
            duration = data["routes"][0]["duration"] / 60  # Convert seconds to minutes
            route_coords = data["routes"][0]["geometry"]["coordinates"]
            return duration, route_coords
        else:
            print(f"OSRM API Error: {data.get('message', 'Unknown error')}")
            return None, None
            
    except Exception as e:
        print(f"Error: {e}")
        return None, None

# Find the nearest fire station based on travel time
best_time = float('inf')
best_station = None
best_route = None

for station in fire_stations:
    duration, route_coords = get_fastest_route(station, fire_location)
    if duration is not None and route_coords:
        print(f"Fire Station {fire_stations.index(station) + 1}: {duration:.1f} minutes")
        if duration < best_time:
            best_time = duration
            best_station = station
            best_route = route_coords

# Create a Folium Map
m = folium.Map(location=fire_location, zoom_start=12)

# Add fire location marker
folium.Marker(
    fire_location, 
    popup="Wildfire Location", 
    icon=folium.Icon(color="red", icon="fire")
).add_to(m)

# Add fire stations markers
marker_cluster = MarkerCluster().add_to(m)
for idx, station in enumerate(fire_stations):
    folium.Marker(
        station,
        popup=f"Fire Station {idx+1}",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(marker_cluster)

# Draw the best route
if best_station and best_route:
    folium.PolyLine(
        locations=[(lat, lon) for lon, lat in best_route],
        color="blue",
        weight=5,
        opacity=0.7,
        popup=f"Best Route: {best_time:.1f} minutes"
    ).add_to(m)
    print(f"Found best route: {best_time:.1f} minutes")
else:
    print("No valid route found.")

# Save and display the map
m.save("generated_map.html")
print("Map saved as 'generated_map.html'. Open it in your browser.")

