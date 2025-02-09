from flask import Flask, jsonify
from flask_cors import CORS  # This allows cross-origin requests from your frontend

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Import the routes for our application
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
