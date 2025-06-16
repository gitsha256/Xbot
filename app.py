import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import tweepy

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: app.py started loading (top of file)")

app = Flask(__name__)
print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask app object 'app' created.")

# ... (rest of your app.py code)

# Place the initialization of the Twitter client outside the route
# so it runs when preload_app = True attempts to load the app.
try:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Attempting early Twitter client initialization...")
    GLOBAL_TWITTER_CLIENT = initialize_twitter_client()
    if GLOBAL_TWITTER_CLIENT:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialized successfully.")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialization FAILED (returned None). Check env vars or API keys.")
except Exception as e:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: EXCEPTION during early Twitter client initialization: {e}")
    GLOBAL_TWITTER_CLIENT = None # Ensure it's None on failure

@app.route('/')
def index():
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask '/' route accessed.")
    # ... (your route logic)
    return "Test: Flask is running!"

if __name__ == "__main__":
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Running in __main__ block (local development).")
    # ... (your local server start code)
