# Wildfire Management System

## Overview
The **Wildfire Management System** is a real-time application designed to predict wildfire spread, assess risks, and optimize the allocation of firefighting resources such as firefighters, water tankers, and aircraft. The system uses machine learning models to forecast fire spread based on weather and environmental data, and then applies optimization algorithms to ensure the most efficient use of available resources. The goal is to minimize damage, enhance emergency response, and protect lives and infrastructure.

![Wild Fire Map](https://github.com/NehaSJ99/Wild-Fire-Resource-Management-Optimization/blob/main/firemap.PNG)
![Dashboard](https://github.com/NehaSJ99/Wild-Fire-Resource-Management-Optimization/blob/main/dashboard.PNG)
![Evacuation Map](https://github.com/NehaSJ99/Wild-Fire-Resource-Management-Optimization/blob/main/evacuationMap.PNG)


## Features
- **Fire Spread Prediction:** Uses machine learning models to predict wildfire spread based on historical data, weather patterns, and environmental factors.
- **Risk Assessment:** Assesses the risk level of different areas based on predicted fire spread and real-time data.
- **Resource Optimization:** Optimizes the deployment of firefighting resources, such as fire stations, tankers, and aircraft, based on real-time risk levels.
- **Real-Time Monitoring:** Integrates real-time weather and fire data to update the fire spread predictions and resource allocation continuously.
- **Interactive Dashboard:** A web-based user interface that allows emergency responders to monitor fire spread, risk levels, and resource availability in real time.

## Technologies Used
- **Backend:** Flask (for API development)
- **Frontend:** React.js (for interactive user dashboard)
- **Machine Learning:** Scikit-learn (for predictive models)
- **Data Processing:** Pandas (for handling and processing data)
- **Real-Time Data:** OpenWeatherMap API (for weather data), Google Maps API (for geolocation services)
- **Data Visualization:** D3.js, Plotly (for interactive graphs and mapping)

## Installation

### Prerequisites
- Python 3.x
- Node.js and npm
- Virtualenv (for Python dependencies)

### Backend Setup
1. Clone the repository:
   ```
   git clone https://github.com/NehaSJ99/wildfire-management-system.git
   cd wildfire-management-system/backend
   ```

2. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the Flask server:
   ```
   python app.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd ../frontend
   ```

2. Install the required npm packages:
   ```
   npm install
   ```

3. Start the React development server:
   ```
   npm start
   ```

The application should now be running locally on `http://localhost:3000`.

## Usage
- The **Wildfire Management System** provides real-time predictions and risk assessments based on incoming weather and environmental data.
- Users can monitor wildfire spread and resource allocation via the interactive dashboard.
- The system will automatically optimize resource allocation based on the predicted fire spread and real-time data, helping firefighting teams respond more effectively.

## Challenges Faced
- Integrating real-time weather data and ensuring the fire prediction model was accurate enough for real-world applications.
- Optimizing resource allocation while balancing limited resources against the urgency of fire response.
- Designing an intuitive and efficient user interface to present complex data in a clear, actionable way.

## What's Next
- Improve prediction accuracy by integrating more granular data such as terrain types and vegetation.
- Expand the system to include additional resources like evacuation plans, medical teams, and shelters.
- Explore the integration of satellite imagery and drone data for enhanced wildfire monitoring and resource allocation.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
