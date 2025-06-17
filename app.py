import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import tweepy
import schedule # Still imported for type hinting or if functions might be called elsewhere
import time     # Still imported for type hinting or if functions might be called elsewhere
import threading # Still imported for type hinting or if functions might be called elsewhere
import requests
import random
from pytrends.request import TrendReq

# --- Debugging print at the very top of the file ---
print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: app.py started loading (top of file)")

# --- Flask App Initialization ---
app = Flask(__name__)
print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask app object 'app' created")

# --- Function Definitions (MUST be defined before they are called globally) ---

def validate_env_vars():
    """
    Validates that all required environment variables are set.
    Prints missing variables for debugging.
    """
    required_vars = ["BEARER_TOKEN", "API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET", "NEWS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Missing environment variables: {missing_vars}")
        return False
    # Print 'Set' for sensitive variables for confirmation, not actual values
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Environment variables: { {k: 'Set' for k in required_vars} }")
    return True

def initialize_twitter_client():
    """
    Initializes and returns a Tweepy Twitter client.
    Handles environment variable loading (for local dev) and validation.
    """
    try:
        # load_dotenv() is primarily for local development.
        # On Railway, environment variables are set directly in the service settings.
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

def fetch_news_article():
    """
    Fetches a random news article from NewsAPI and formats it for a tweet.
    """
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching news article...")
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            raise ValueError("NEWS_API_KEY not set.")

        categories = ['technology', 'entertainment', 'sports', 'business', 'health']
        category = random.choice(categories)
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={news_api_key}"

        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        articles = data.get("articles")

        if not articles:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: No News API articles found.")
            return None

        article = random.choice(articles)
        title = article['title']
        source_name = article['source']['name']
        url = article['url']

        tweet = f"{title} 📰\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}"

        # Truncate tweet if it's too long for Twitter's 280 character limit
        if len(tweet) > 280:
            # Calculate max length for title, accounting for fixed suffix length
            fixed_suffix_len = len(f"\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}")
            max_title_len = 280 - fixed_suffix_len - 3 # -3 for "..."
            tweet = f"{title[:max_title_len]}...\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}"

        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API fetch failed (RequestException): {e}")
        return None
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API unexpected error: {e}")
        return None

def fetch_random_fact():
    """
    Fetches a random useless fact and formats it for a tweet.
    Falls back to news article if fact fetching fails.
    """
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching random fact...")
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=10)
        response.raise_for_status()
        fact = response.json().get("text")
        tweet = f"Did you know? {fact} 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"

        if len(tweet) > 280:
            # Truncate fact to ensure tweet fits, adding "..."
            tweet = f"Did you know? {fact[:200]}... 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"

        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Random fact tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Random fact fetch failed (RequestException): {e}")
        # Fallback to news article if random fact fails
        return fetch_news_article()
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Random fact unexpected error: {e}")
        return fetch_news_article()

def fetch_google_trends():
    """
    Fetches a trending search from Google Trends and formats it for a tweet.
    Falls back to news article if trend fetching fails.
    """
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching Google Trends...")
        # TrendReq can sometimes be slow; longer timeout for its internal requests
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        trending_df = pytrends.trending_searches(pn='US')

        if trending_df.empty:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: No Google Trends data found.")
            return fetch_news_article() # Fallback

        trend_name = random.choice(trending_df[0].tolist())
        hashtag = trend_name.replace(' ', '').replace('#', '') # Create simple hashtag

        tweet = f"Trending on Google: '{trend_name}' 🔥\n\nWhat's driving this buzz? #GoogleTrends #{hashtag}"

        if len(tweet) > 280:
            # Truncate trend_name and hashtag if tweet is too long
            tweet = f"Trending: '{trend_name[:50]}...' 🔥\n\nWhat's driving this? #GoogleTrends #{hashtag[:20]}"

        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Google Trends tweet generated: {tweet[:50]}...")
        return tweet
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Google Trends fetch failed: {e}")
        return fetch_news_article() # Fallback

def get_tweet_content():
    """
    Selects a random content source and fetches content for a tweet.
    """
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching tweet content...")
    sources = ['news_api', 'news_api', 'google_trends', 'random_fact'] # More weight to news
    source = random.choice(sources)
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Selected source: {source}")

    if source == 'news_api':
        return fetch_news_article()
    elif source == 'google_trends':
        return fetch_google_trends()
    else: # random_fact
        return fetch_random_fact()

def post_tweets(client):
    """
    Posts a batch of tweets with delays.
    Handles rate limits and other Tweepy exceptions.
    """
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting tweet batch...")
    max_tweets = 4 # Reduce number of tweets per batch initially
    # Set a generous delay between individual tweets (e.g., 30 minutes)
    # This is more important than spreading across the whole 3-hour window
    individual_tweet_delay_seconds = 30 * 60 # 30 minutes

    for i in range(max_tweets):
        if not client:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} skipped: Twitter client not initialized.")
            break

        content = get_tweet_content()
        if content:
            try:
                # Ensure the tweet is within limits before attempting to post
                if len(content) > 280:
                    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Tweet content too long, truncating before posting.")
                    content = content[:277] + "..." # Truncate and add ellipsis

                client.create_tweet(text=content)
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} posted: {content[:50]}...")
            except tweepy.errors.TooManyRequests as e:
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Rate limit hit: {e}. Waiting 15 minutes before retrying.")
                time.sleep(15 * 60 + 10) # Add a small buffer just in case
                continue # Try the current tweet again
            except tweepy.TweepyException as e:
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Failed to post tweet {i+1}/{max_tweets} (TweepyException): {e}. Waiting 60 seconds.")
                time.sleep(60)
                continue
            except Exception as e:
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Unexpected error posting tweet {i+1}/{max_tweets}: {e}. Skipping tweet.")
                pass

        else:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: No content generated for tweet {i+1}/{max_tweets}, skipping.")

        # Always sleep after an attempt (whether successful or not, unless continued for rate limit)
        # This ensures you respect the individual tweet delay.
        if i < max_tweets - 1: # Don't sleep after the last tweet of the batch
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Waiting {individual_tweet_delay_seconds/60} minutes before next tweet...")
            time.sleep(individual_tweet_delay_seconds)

    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Finished tweet batch.")


def run_schedule(client):
    """
    Sets up and runs the tweeting schedule.
    This function will be run in the separate worker process.
    """
    # Schedule post_tweets to run every 3 hours
    schedule.every(3).hours.do(post_tweets, client=client)
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler set to run post_tweets every 3 hours.")

    # Run post_tweets immediately when the scheduler starts
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Running initial tweet batch...")
    post_tweets(client)

    # Infinite loop to keep the scheduler running
    while True:
        try:
            schedule.run_pending()
            time.sleep(10) # Check for pending jobs every 10 seconds
        except Exception as e:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler error: {e}. Waiting 60 seconds before retrying loop.")
            time.sleep(60) # Wait on error to prevent rapid logging


# --- Global Initialization for Gunicorn (with preload_app=True) ---
# This block is executed when Gunicorn imports app.py due to preload_app = True.
# The `app` object and GLOBAL_TWITTER_CLIENT are set up here for all workers.
try:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Attempting early Twitter client initialization for preload_app.")
    GLOBAL_TWITTER_CLIENT = initialize_twitter_client()
    if GLOBAL_TWITTER_CLIENT:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialized successfully.")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialization FAILED (returned None). Check Railway env vars or API keys.")
except Exception as e:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: EXCEPTION during early Twitter client initialization: {e}")
    GLOBAL_TWITTER_CLIENT = None

# --- Flask Route Definitions ---

@app.route('/')
def index():
    """
    Main Flask route. Simple check to see if the app is running.
    """
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask '/' route accessed.")
    if GLOBAL_TWITTER_CLIENT:
        return "Test: Flask web server is running and Twitter client initialized for web requests!"
    else:
        return "Test: Flask web server is running, but Twitter client failed to initialize."


# --- Main block for local development execution (ONLY runs when `python app.py` is called directly) ---
if __name__ == "__main__":
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server in __main__ block (local development).")

    # For local development, you might want to initialize the client separately
    # or use the GLOBAL_TWITTER_CLIENT if it was initialized above.
    # The scheduler thread will NOT run when Gunicorn is managing the app.
    local_dev_client = initialize_twitter_client()

    if local_dev_client:
        # Start the scheduler as a thread ONLY for local development
        # On Railway, this will be handled by the separate 'worker' process.
        scheduler_thread = threading.Thread(target=run_schedule, args=(local_dev_client,), daemon=True)
        scheduler_thread.start()
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler thread started for local development.")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Twitter client not initialized, skipping scheduler for local development.")

    port = int(os.environ.get("PORT", 8080))
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port} (local development)...")
    app.run(host='0.0.0.0', port=port)

