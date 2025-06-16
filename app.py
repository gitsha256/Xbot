from flask import Flask
from dotenv import load_dotenv
from datetime import datetime
import tweepy
import schedule
import time
import threading
import requests
import random
from pytrends.request import TrendReq
import os

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: app.py started loading (top of file)")

app = Flask(__name__)

print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask app object 'app' created")

# --- All Function Definitions Must Come First ---

def validate_env_vars():
    required_vars = ["BEARER_TOKEN", "API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET", "NEWS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Missing environment variables: {missing_vars}")
        return False
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Environment variables: { {k: 'Set' for k in required_vars} }")
    return True

def initialize_twitter_client():
    try:
        load_dotenv() # For local dev, Railway sets env vars directly
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
    # ... (your existing fetch_news_article function) ...
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching news article...")
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            raise ValueError("NEWS_API_KEY not set.")
        categories = ['technology', 'entertainment', 'sports', 'business', 'health']
        category = random.choice(categories)
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={news_api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
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
        if len(tweet) > 280:
            max_title_len = 280 - len(f"\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}")
            tweet = f"{title[:max_title_len]}...\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}"
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API fetch failed: {e}")
        return None
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: News API unexpected error: {e}")
        return None

def fetch_random_fact():
    # ... (your existing fetch_random_fact function) ...
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching random fact...")
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=10)
        response.raise_for_status()
        fact = response.json().get("text")
        tweet = f"Did you know? {fact} 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        if len(tweet) > 280:
            tweet = f"Did you know? {fact[:200]}... 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Random fact tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Random fact fetch failed: {e}")
        return fetch_news_article()

def fetch_google_trends():
    # ... (your existing fetch_google_trends function) ...
    try:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching Google Trends...")
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        trending_df = pytrends.trending_searches(pn='US')
        if trending_df.empty:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: No Google Trends data found.")
            return fetch_news_article()
        trend_name = random.choice(trending_df[0].tolist())
        hashtag = trend_name.replace(' ', '').replace('#', '')
        tweet = f"Trending on Google: '{trend_name}' 🔥\n\nWhat's driving this buzz? #GoogleTrends #{hashtag}"
        if len(tweet) > 280:
            tweet = f"Trending: '{trend_name[:50]}...' 🔥\n\nWhat's driving this? #GoogleTrends #{hashtag[:20]}"
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Google Trends tweet generated: {tweet[:50]}...")
        return tweet
    except Exception as e:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Google Trends fetch failed: {e}")
        return fetch_news_article()

def get_tweet_content():
    # ... (your existing get_tweet_content function) ...
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Fetching tweet content...")
    sources = ['news_api', 'news_api', 'google_trends', 'random_fact']
    source = random.choice(sources)
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Selected source: {source}")
    if source == 'news_api':
        return fetch_news_article()
    elif source == 'google_trends':
        return fetch_google_trends()
    else:
        return fetch_random_fact()

def post_tweets(client):
    # ... (your existing post_tweets function) ...
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting tweet batch...")
    max_tweets = 8
    delay = (3 * 60 * 60) / max_tweets
    for i in range(max_tweets):
        if not client:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} skipped: Twitter client not initialized.")
            break
        content = get_tweet_content()
        if content:
            try:
                client.create_tweet(text=content)
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} posted: {content[:50]}...")
            except tweepy.errors.TooManyRequests as e:
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Rate limit hit: {e}. Waiting 15 minutes.")
                time.sleep(15 * 60)
                continue
            except tweepy.TweepyException as e:
                print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Failed to post tweet {i+1}/{max_tweets}: {e}")
                time.sleep(60)
                continue
        else:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: No content for tweet {i+1}/{max_tweets}, skipping.")
        time.sleep(delay)
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Finished tweet batch.")

def run_schedule(client):
    # ... (your existing run_schedule function) ...
    schedule.every(3).hours.do(post_tweets, client=client)
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler started, running every 3 hours...")
    post_tweets(client) # Run immediately on startup
    while True:
        try:
            schedule.run_pending()
            time.sleep(10)
        except Exception as e:
            print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler error: {e}")
            time.sleep(60)

# --- Flask Route Definition ---

@app.route('/')
def index():
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Flask route accessed")
    return "Test: Flask is running!"

# --- Entry Point for Local Development or Gunicorn (when not preloading directly from global scope) ---

# This block ensures that the scheduler thread is ONLY started when app.py is run directly
# (e.g., python app.py), or when Gunicorn runs it without preload_app=True (less common for this setup)
# For preload_app=True, the worker's import will call initialize_twitter_client() directly.

# --- Global Initialization for Gunicorn (with preload_app=True) ---
# This block will be executed by Gunicorn when preload_app is true
try:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Attempting early Twitter client initialization for preload_app.")
    GLOBAL_TWITTER_CLIENT = initialize_twitter_client()
    if GLOBAL_TWITTER_CLIENT:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialized successfully.")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Global Twitter client initialization FAILED (returned None). Check Railway env vars or API keys.")
except Exception as e:
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%M:%S')}]: EXCEPTION during early Twitter client initialization: {e}")
    GLOBAL_TWITTER_CLIENT = None

# --- Main block for local execution ---
if __name__ == "__main__":
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting minimal Flask app in __main__ block (local development).")

    # In local development, we re-initialize the client explicitly here
    # as the GLOBAL_TWITTER_CLIENT might already be set by Gunicorn's preload (if running both ways)
    # or to ensure it's fresh for local testing.
    local_client = initialize_twitter_client()

    if local_client:
        scheduler_thread = threading.Thread(target=run_schedule, args=(local_client,), daemon=True)
        scheduler_thread.start()
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Scheduler thread started (local development)")
    else:
        print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Twitter client not initialized, skipping scheduler (local development)")

    port = int(os.environ.get("PORT", 8080))
    print(f"DEBUG_RAILWAY [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port} (local development)...")
    app.run(host='0.0.0.0', port=port)
