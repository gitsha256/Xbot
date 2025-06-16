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
print("ENV VARS:", dict(os.environ))


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --- Twitter Authentication ---
try:
    load_dotenv()

    bearer_token = os.getenv("BEARER_TOKEN")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    assert all([bearer_token, api_key, api_secret, access_token, access_token_secret]), "One or more Twitter API credentials are missing."

    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    username = client.get_me().data.username
    logger.info(f"Authenticated as {username}")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Successfully authenticated as {username}")
except Exception as e:
    logger.error(f"Failed to initialize Tweepy Client: {e}")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Authentication failed: {e}")
    exit(1)

# --- Helper Function for News API ---
def fetch_news_article():
    """
    Fetches a news article from News API as primary or fallback content.
    """
    try:
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            logger.error("NEWS_API_KEY environment variable not set.")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: NEWS_API_KEY not set.")
            return None

        categories = ['technology', 'entertainment', 'sports', 'business', 'health']
        category = random.choice(categories)
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={news_api_key}"

        response = requests.get(url)
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
    """
    Fetches a random fact from uselessfacts.jsph.pl.
    """
    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
        response.raise_for_status()
        fact = response.json().get("text")
        
        tweet = f"Did you know? {fact} 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        if len(tweet) > 280:
            tweet = f"Did you know? {fact[:200]}... 🤯\n\nShare your thoughts! #FunFact #DidYouKnow"
        
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Random fact tweet generated: {tweet[:50]}...")
        return tweet
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch random fact: {e}")
        print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Random fact fetch failed: {e}")
        return fetch_news_article()  # Fallback to News API

# --- Tweet Content Generation ---
def get_tweet_content():
    """
    Fetches content from News API, Google Trends, or random facts randomly, with fallback to News API.
    """
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Fetching tweet content...")
    sources = ['news_api', 'news_api', 'google_trends', 'random_fact']  # Weight News API higher
    source = random.choice(sources)
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Selected source: {source}")

    if source == 'news_api':
        return fetch_news_article()

    elif source == 'google_trends':
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
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
            
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Google Trends tweet generated: {tweet[:50]}...")
            return tweet

        except Exception as e:
            logger.error(f"Failed to fetch Google Trends: {e}")
            print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Google Trends fetch failed: {e}")
            return fetch_news_article()  # Fallback to News API

    else:  # random_fact
        return fetch_random_fact()

# --- Tweeting Function ---
def post_tweets():
    """
    Posts up to 8 tweets in a batch with rate limit handling.
    """
    logger.info("Starting a batch of up to 8 tweets.")
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting tweet batch...")
    max_tweets = 8
    delay = (3 * 60 * 60) / max_tweets  # 3 hours divided by 8 tweets (~22.5 minutes each)

    for i in range(max_tweets):
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
def run_schedule():
    """
    Schedules tweet batches and prints next post time.
    """
    # Temporary schedule for testing: run every 2 minutes
    schedule.every(2).minutes.do(post_tweets)
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Scheduler started, running every 2 minutes for testing.")
    
    # Run one batch immediately for testing
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Running immediate test batch...")
    post_tweets()

    last_print_time = 0
    while True:
        schedule.run_pending()
        current_time = time.time()
        # Print every 30 seconds
        if current_time - last_print_time >= 30:
            next_run = schedule.next_run()
            if next_run:
                next_run_str = next_run.strftime('%H:%M:%S %Y-%m-%d')
                print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Checking schedule... Next post batch at {next_run_str}")
            else:
                print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Checking schedule... No scheduled posts.")
            last_print_time = current_time
        time.sleep(1)

# --- Web Server ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Your Twitter Bot is up and running!"

if __name__ == "__main__":
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Twitter bot...")
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    port = int(os.environ.get("PORT", 8080))
    print(f"TEST [{datetime.now().strftime('%H:%M:%S')}]: Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
