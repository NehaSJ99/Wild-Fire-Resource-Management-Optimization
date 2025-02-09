from flask import jsonify
from app import app

# Route for predicting the spread of fire
@app.route("/predict_spread", methods=["POST"])
def predict_spread():
    # Here, you can call the actual model or algorithm to predict the spread.
    # For now, it's a dummy response.
    # Example: you could integrate machine learning models, data processing, etc.

    response = {
        "status": "success",
        "message": "Fire spread prediction completed successfully",
        "prediction": {
            "spread_rate": 12.5,  # Example output
            "area_affected": 2500,  # Example output
        },
    }
    return jsonify(response)


# Route for optimizing resources
@app.route("/resource_optimization", methods=["GET", "POST"])
def resource_optimization():
    try:
        # Execute the `resource_optimized.py` script
        result = subprocess.run(["python", "resource_optimized.py"], capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            return jsonify({"status": "error", "message": "Error executing script", "error": result.stderr}), 500

        # Parse JSON output from the script
        output = json.loads(result.stdout)
        
        return jsonify({"status": "success", "data": output})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Route for the emergency evacuation plan
@app.route("/evacuation_plan", methods=["POST"])
def evacuation_plan():
    # Logic for creating or retrieving an evacuation plan would go here.
    # This is a placeholder response.
    
    response = {
        "status": "success",
        "message": "Emergency evacuation plan created successfully",
        "evacuation_routes": [
            "Route A: 5 km",
            "Route B: 3 km",
            "Route C: 8 km",
        ],
    }
    return jsonify(response)
