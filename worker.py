import os
import threading
import time
import schedule
from datetime import datetime

# Import the necessary functions from app.py
# Make sure app.py is structured so these functions are importable
from app import initialize_twitter_client, post_tweets, run_schedule

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker process starting...")

# Initialize client for this worker process
worker_client = initialize_twitter_client()

if worker_client:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client initialized, starting scheduler.")
    # The run_schedule function already includes the initial post_tweets call and the loop
    run_schedule(worker_client)
else:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client NOT initialized. Scheduler will not run.")
    # You might want to exit the worker process gracefully here if initialization fails
    exit(1)
