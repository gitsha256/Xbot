import tweepy
import os
import logging
import schedule
import time
import requests
import threading
import random
from flask import Flask
from dotenv import load_dotenv
from pytrends.request import TrendReq
from datetime import datetime

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# --- Environment Variable Validation ---
def validate_env_vars():
    """Validate required environment variables."""
    required_vars = ["BEARER_TOKEN", "API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET", "NEWS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Missing environment variables: {missing_vars}")
        return False
    logger.info("All required environment variables are set.")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Environment variables: { {k: 'Set' for k in required_vars} }")
    return True

# --- Twitter Authentication ---
def initialize_twitter_client():
    """Initialize Tweepy client with error handling."""
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

        username = client.get_me().data.username
        logger.info(f"Authenticated as {username}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Successfully authenticated as {username}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Tweepy Client: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Authentication failed: {e}")
        return None

# --- Helper Function for News API ---
def fetch_news_article():
    """Fetches a news article from News API as primary or fallback content."""
    try:
        logger.info("Fetching news article...")
        news_api_key = os.getenv("NEWS_API_KEY")
        logger.info(f"News API Key: {'Set' if news_api_key else 'Not set'}")
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
            logger.info("No articles found in News API response.")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: No News API articles found.")
            return None

        article = random.choice(articles)
        title = article['title']
        source_name = article['source']['name']
        url = article['url']

        tweet = f"{title} 📰\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}"
        if len(tweet) > 280:
            max_title_len = 280 - len(f"\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}")
            tweet = f"{title[:max_title_len]}...\n\n(Source: {source_name})\nWhat's your take? #{category.capitalize()} #News\n{url}"

        logger.info(f"News API tweet generated: {tweet[:50]}...")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: News API tweet generated: {tweet[:50]}...")
        return tweet

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch News API content: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: News API fetch failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in News API fetch: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: News API unexpected error: {e}")
        return None

# --- Helper Function for Random Fact ---
def fetch_random_fact():
    """Fetches a random fact from uselessfacts.jsph.pl."""
    try:
        logger.info("Fetching random fact...")
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=10)
        response.raise_for_status()
        fact = response.json().get("text")
        
        tweet = f"Did you know? {fact} 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        if len(tweet) > 280:
            tweet = f"Did you know? {fact[:200]}... 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        
        logger.info(f"Random fact tweet generated: {tweet[:50]}...")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Random fact tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch random fact: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Random fact fetch failed: {e}")
        return fetch_news_article()

# --- Helper Function for Google Trends ---
def fetch_google_trends():
    """Fetches trending topics from Google Trends."""
    try:
        logger.info("Fetching Google Trends...")
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        trending_df = pytrends.trending_searches(pn='US')

        if trending_df.empty:
            logger.info("No Google Trends data found.")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: No Google Trends data found.")
            return fetch_news_article()

        trend_name = random.choice(trending_df[0].tolist())
        hashtag = trend_name.replace(' ', '').replace('#', '')
        tweet = f"Trending on Google: '{trend_name}' 🔥\n\nWhat's driving this buzz? #GoogleTrends #{hashtag}"
        
        if len(tweet) > 280:
            tweet = f"Trending: '{trend_name[:50]}...' 🔥\n\nWhat's driving this? #GoogleTrends #{hashtag[:20]}"
        
        logger.info(f"Google Trends tweet generated: {tweet[:50]}...")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Google Trends tweet generated: {tweet[:50]}...")
        return tweet

    except Exception as e:
        logger.error(f"Failed to fetch Google Trends: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Google Trends fetch failed: {e}")
        return fetch_news_article()

# --- Tweet Content Generation ---
def get_tweet_content():
    """Fetches content from News API, Google Trends, or random facts."""
    logger.info("Fetching tweet content...")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Fetching tweet content...")
    sources = ['news_api', 'news_api', 'google_trends', 'random_fact']  # Weight News API higher
    source = random.choice(sources)
    logger.info(f"Selected source: {source}")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Selected source: {source}")

    if source == 'news_api':
        return fetch_news_article()
    elif source == 'google_trends':
        return fetch_google_trends()
    else:
        return fetch_random_fact()

# --- Tweeting Function ---
def post_tweets(client):
    """Posts up to 8 tweets in a batch with rate limit handling."""
    logger.info("Starting a batch of up to 8 tweets.")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting tweet batch...")
    max_tweets = 8
    delay = (3 * 60 * 60) / max_tweets  # 3 hours divided by 8 tweets (~22.5 minutes each)

    for i in range(max_tweets):
        if not client:
            logger.error(f"Tweet {i+1}/{max_tweets} skipped: Twitter client not initialized.")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} skipped: Twitter client not initialized.")
            break

        content = get_tweet_content()
        if content:
            try:
                client.create_tweet(text=content)
                logger.info(f"Tweet {i+1}/{max_tweets} posted: {content[:50]}...")
                print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Tweet {i+1}/{max_tweets} posted: {content[:50]}...")
            except tweepy.errors.TooManyRequests as e:
                logger.warning(f"Rate limit hit: {e}. Waiting 15 minutes.")
                print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Rate limit hit: {e}. Waiting 15 minutes.")
                time.sleep(15 * 60)
                continue
            except tweepy.TweepyException as e:
                logger.error(f"Failed to post tweet {i+1}/{max_tweets}: {e}")
                print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Failed to post tweet {i+1}/{max_tweets}: {e}")
                time.sleep(60)
                continue
        else:
            logger.warning(f"No content for tweet {i+1}/{max_tweets}, skipping.")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: No content for tweet {i+1}/{max_tweets}, skipping.")
        time.sleep(delay)
    logger.info("Finished posting tweet batch.")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Finished tweet batch.")

# --- Scheduling ---
def run_schedule(client):
    """Schedules tweet batches and logs next post time."""
    # Schedule for every 2 minutes for testing; adjust to 3 hours for production
    # For production, use: schedule.every(3).hours.do(post_tweets, client=client)
    schedule.every(2).minutes.do(post_tweets, client=client)
    logger.info("Scheduler started, running every 2 minutes for testing.")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Scheduler started, running every 2 minutes for testing.")
    
    # Run one batch immediately for testing
    logger.info("Running immediate test batch...")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Running immediate test batch...")
    post_tweets(client)

    last_print_time = 0
    while True:
        try:
            schedule.run_pending()
            current_time = time.time()
            if current_time - last_print_time >= 30:
                next_run = schedule.next_run()
                if next_run:
                    next_run_str = next_run.strftime('%H:%M:%S %Y-%m-%d')
                    logger.info(f"Checking schedule... Next post batch at {next_run_str}")
                    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Checking schedule... Next post batch at {next_run_str}")
                else:
                    logger.info("Checking schedule... No scheduled posts.")
                    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Checking schedule... No scheduled posts.")
                last_print_time = current_time
            time.sleep(10)  # Increased sleep to reduce CPU usage
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Scheduler error: {e}")
            time.sleep(60)

# --- Web Server ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Your Twitter Bot is up and running!"

if __name__ == "__main__":
    logger.info("Starting Twitter bot...")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Twitter bot...")
    
    # Initialize Twitter client
    client = initialize_twitter_client()
    
    # Start scheduler in a separate thread
    if client:
        scheduler_thread = threading.Thread(target=run_schedule, args=(client,), daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler thread started.")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Scheduler thread started.")
    else:
        logger.error("Twitter client not initialized, skipping scheduler.")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Twitter client not initialized, skipping scheduler.")

    # Start Flask app
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask server on port {port}...")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
