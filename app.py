import os
from flask import Flask
from datetime import datetime

print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Module loaded")

app = Flask(__name__)

print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Flask app initialized")

@app.route('/')
def index():
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Flask route accessed")
    return "Test: Flask is running!"

if __name__ == "__main__":
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting minimal Flask app...")
    port = int(os.environ.get("PORT", 8080))
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
