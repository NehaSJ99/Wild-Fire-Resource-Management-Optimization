from flask import Flask, jsonify, request, send_from_directory
from app import app
import tensorflow as tf 
import subprocess
import json
import os

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
    try:
        # Execute the Python script for resource optimization
        result = subprocess.run(['python', 'resource_optimized.py'], capture_output=True, text=True)

        if result.returncode == 0:
            # Attempt to parse the JSON output from the script
            try:
                output = json.loads(result.stdout)  # Parse the JSON output from the script
                return jsonify({'status': 'success', 'data': output})
            except json.JSONDecodeError as json_err:
                return jsonify({'status': 'error', 'message': 'Failed to decode JSON from script output', 'error': str(json_err)}), 500
        else:
            return jsonify({'status': 'error', 'message': 'Script execution failed', 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    '''
    # Example data
    optimized_resources = {
        "firefighters": 50,
        "trucks": 10,
        "helicopters": 5
    }
    return jsonify({
        "status": "success",
        "resources_allocated": optimized_resources
    })'''
    


# Route for the emergency evacuation plan
@app.route('/generate_map')
def generate_map():
    try:
        # Run map.py to generate the map
        result = subprocess.run(['python', 'map.py'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Log the output of map.py for debugging
        print("Output:", result.stdout.decode())
        print("Error:", result.stderr.decode())

        # After map.py runs, the generated_map.html file will be saved in the static directory
        return "Map generated successfully. <a href='/evacuation_map'>View the map</a>"

    except subprocess.CalledProcessError as e:
        print("Error generating map:", e)
        print("Error output:", e.stderr.decode())  # Log error output from map.py
        return "Error generating the map", 500


@app.route('/evacuation_map')
def serve_map():
    # Ensure the path to static is correct
    return send_from_directory(os.getcwd(), 'generated_map.html')


