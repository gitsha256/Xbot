import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import tweepy

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: app.py started loading (top of file)")

app = Flask(__name__)
print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask app object 'app' created.")

# --- Function Definitions MUST come BEFORE they are called globally ---

def validate_env_vars():
    required_vars = ["BEARER_TOKEN", "API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Missing environment variables: {missing_vars}")
        return False
    # Only print "Set" for clarity, actual values are sensitive
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Environment variables: { {k: 'Set' for k in required_vars} }")
    return True

def initialize_twitter_client():
    try:
        # load_dotenv() is typically for local development; Railway handles env vars directly
        # You can keep it, but it won't load from a .env file on Railway
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
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Twitter client initialized")
        return client
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Authentication failed: {e}")
        return None

# --- Global Scope Calls (after functions are defined) ---

try:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Attempting early Twitter client initialization for preload_app.")
    GLOBAL_TWITTER_CLIENT = initialize_twitter_client() # This call is now after definition
    if GLOBAL_TWITTER_CLIENT:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialized successfully.")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialization FAILED (returned None). Check Railway env vars or API keys.")
except Exception as e:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: EXCEPTION during early Twitter client initialization: {e}")
    GLOBAL_TWITTER_CLIENT = None

# --- Flask Routes ---

@app.route('/')
def index():
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask '/' route accessed.")
    # You might want to use GLOBAL_TWITTER_CLIENT here if it was successfully initialized
    # client = GLOBAL_TWITTER_CLIENT
    # For now, just return a simple message
    if GLOBAL_TWITTER_CLIENT:
        return "Test: Flask is running and Twitter client initialized!"
    else:
        return "Test: Flask is running, but Twitter client failed to initialize."


# --- Local Development Server (only runs if app.py is executed directly) ---

if __name__ == "__main__":
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Running in __main__ block (local development).")
    # In local development, you might re-initialize here or handle client differently
    # client = initialize_twitter_client() # Example, depends on your local setup
    port = int(os.environ.get("PORT", 8080))
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
