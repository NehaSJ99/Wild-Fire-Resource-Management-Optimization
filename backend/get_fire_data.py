# fetch_fire_data.py
import pandas as pd

# 🔹 Replace with your NASA FIRMS API Key
MAP_KEY = "546e11b1bdba71b1496bc9e918f93b57"

def get_fire_data(country_code="IND", days=3):
    """Fetch fire data from NASA FIRMS API and return as JSON."""
    base_url = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/"
    url = f"{base_url}{MAP_KEY}/MODIS_NRT/{country_code}/{days}"

    try:
        df = pd.read_csv(url)

        # Convert DataFrame to JSON
        fire_data = df.to_dict(orient="records")
        return fire_data

    except Exception as e:
        print(f"🔥 Error fetching fire data: {e}")
        return []
