import os
import threading
import time
import schedule
from datetime import datetime

# IMPORTANT: These functions are imported from app.py.
# Ensure their definitions in app.py are at the top level (not inside if __name__ == "__main__":)
# so they are importable.
from app import initialize_twitter_client, post_tweets, run_schedule

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker process starting...")

# Initialize the Twitter client specifically for this worker process.
# This ensures the worker has its own authenticated client and doesn't rely on the web process's client.
# It will use the environment variables configured in Railway.
worker_client = initialize_twitter_client()

if worker_client:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client initialized successfully for scheduler.")
    # The run_schedule function already contains the logic to:
    # 1. Set up the 'every 3 hours' schedule.
    # 2. Run the post_tweets batch immediately.
    # 3. Enter an infinite loop to keep the scheduler running and check pending jobs.
    run_schedule(worker_client)
else:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Worker client NOT initialized. Scheduler will not run.")
    # If client initialization fails, it's critical for the worker to indicate an error.
    # Railway will then likely detect this and attempt to restart the worker.
    exit(1)

