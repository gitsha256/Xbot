# worker.py
import os
import threading
import time
import schedule
from datetime import datetime

# Import the functions needed from app.py
from app import initialize_twitter_client, post_tweets, run_schedule

# Initialize client for the worker process
print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker process starting...")
worker_client = initialize_twitter_client()

if worker_client:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client initialized, starting scheduler.")
    run_schedule(worker_client)
else:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client NOT initialized. Scheduler will not run.")
    # You might want to exit or log an error more prominently here
