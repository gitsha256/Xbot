import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import tweepy

print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Module loaded")

app = Flask(__name__)

print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Flask app initialized")

def validate_env_vars():
    required_vars = ["BEARER_TOKEN", "API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Missing environment variables: {missing_vars}")
        return False
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Environment variables: { {k: 'Set' for k in required_vars} }")
    return True

def initialize_twitter_client():
    try:
        load_dotenv()
        if not validate_env_vars():
            raise ValueError("Environment variable validation failed.")
        client = tweepy.Client(
            bearer_token=os.getenv("BEARER_TOKEN"),
            consumer_key=os.getenv("API_KEY"),
            consumer_secret=os.getenv("API_SECRET"),
            access_token=os.getenv("ACCESS_TOKEN"),
            access_token_secret=os.getenv("ACCESS_TOKEN_SECRET")
        )
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Twitter client initialized")
        return client
    except Exception as e:
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Authentication failed: {e}")
        return None

@app.route('/')
def index():
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Flask route accessed")
    client = initialize_twitter_client()
    return "Test: Flask is running!"

if __name__ == "__main__":
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting minimal Flask app...")
    client = initialize_twitter_client()
    port = int(os.environ.get("PORT", 8080))
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
