from flask import Flask, jsonify, request
from app import app
import tensorflow as tf 

model = tf.keras.models.load_model('predictions.keras')

# Route for predicting the spread of fire
@app.route("/predict_spread", methods=["POST"])
def predict_spread():
    # Get data from the frontend (e.g., input data for prediction)
    data = request.get_json()
    
    # Perform the prediction (adjust input data as needed)
    prediction_input = data['input_data']  # Assuming the frontend sends input_data
    
    # Make prediction using the model
    prediction = model.predict(prediction_input)
    
    # Return the prediction result
    return jsonify({'prediction': prediction.tolist()})  # Convert to list for JSON serialization


# Route for optimizing resources
@app.route('/optimize_resources', methods=['POST'])  # Ensure the route is exactly this
def optimize_resources():
    response = {
        "status": "success",
        "message": "Resource optimization completed successfully",
        "resources_allocated": {
            "firefighters": 15,
            "trucks": 5,
            "helicopters": 2,
        },
    }
    return jsonify(response)
    '''
    try:
        result = subprocess.run(['python', 'resource_optimized.py'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            return jsonify({'status': 'success', 'data': output})
        else:
            return jsonify({'status': 'error', 'message': 'Script execution failed', 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    '''
    


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
