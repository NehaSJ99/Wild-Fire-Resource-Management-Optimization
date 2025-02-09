from flask import Flask, jsonify
from flask_cors import CORS  # This allows cross-origin requests from your frontend
import os

app = Flask(__name__, static_folder='frontend-new/src/static')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Import the routes for our application
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
