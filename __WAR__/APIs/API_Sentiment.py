# Twitter is expensive as shit. Need to switch to smth different
# Might scavange off of ARTEMIS

import requests, os, time, praw, re
from textblob import TextBlob
import pandas as pd
from praw.exceptions import APIException
from datetime import datetime

class keys_to_the_lambo:
    def __init__(self, API_Reddit_ClientID, API_Reddit_ClientSecret, API_Reddit_ClientUserAgent):
        self.client_id = API_Reddit_ClientID
        self.client_secret = API_Reddit_ClientSecret
        self.user_agent = API_Reddit_ClientUserAgent

    def connect(self):
        reddit = praw.Reddit(
            client_id=self.client_id, 
            client_secret=self.client_secret, 
            user_agent=self.user_agent,
            ratelimit_seconds=True)
        return reddit

class RedditSentimentScraper:
    def __init__(self, API_Reddit_ClientID, API_Reddit_ClientSecret, API_Reddit_ClientUserAgent, log_file="scraped_subreddits.txt"):
        keys = keys_to_the_lambo(API_Reddit_ClientID, API_Reddit_ClientSecret, API_Reddit_ClientUserAgent)
        self.reddit = keys.connect()
        self.log_file = log_file
        self.scraped_subreddits = self.load_scraped_subreddits()
        self.request_delay = 2  # Initial delay between requests (in seconds)

    def load_scraped_subreddits(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as file:
                return set(line.strip() for line in file)
        return set()

    def update_scraped_log(self, subreddit_name):
        with open(self.log_file, "a") as file:
            file.write(subreddit_name + "\n")
        self.scraped_subreddits.add(subreddit_name)

    def search_subreddits(self, prompt, num_subreddits=5):
        subreddits = []
        search_results = self.reddit.subreddits.search_by_name(prompt, include_nsfw=False, exact=False)
        for idx, subreddit in enumerate(search_results):
            if idx >= num_subreddits:
                break
            subreddits.append(subreddit.display_name)
        return subreddits

    def scrape_posts_with_sentiment(self, subreddit_name, limit=100):
        if subreddit_name in self.scraped_subreddits:
            print(f"Skipping {subreddit_name}, already scraped.")
            return [] 
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts_data = []
        for submission in subreddit.top(limit=limit):  # Top posts
            try:
                # Introduce delay between requests to prevent hitting rate limits
                time.sleep(self.request_delay)

                post_title = submission.title
                post_selftext = submission.selftext  # The body text of the post
                sentiment_score = self.analyze_sentiment(post_title + " " + post_selftext)
                comments_sentiment_score = self.analyze_comments_sentiment(submission)
                
                # Add timestamp by converting created_utc to a readable datetime format
                post_timestamp = datetime.utcfromtimestamp(submission.created_utc)
                
                post_data = {
                    'title': post_title,
                    'selftext': post_selftext,
                    'url': submission.url,
                    'upvotes': submission.score,
                    'sentiment_score': sentiment_score,
                    'comments_sentiment_score': comments_sentiment_score,
                    'timestamp': post_timestamp  # Add timestamp
                }
                posts_data.append(post_data)

            except APIException as e:
                # Handle rate limit errors (HTTP 429)
                if "RATELIMIT" in str(e) or "TooManyRequests" in str(e):
                    self.handle_rate_limit(e)

        self.update_scraped_log(subreddit_name)  # Log scraped subreddit
        return posts_data

    def handle_rate_limit(self, e):
        """
        Handles the Reddit API rate limit by extracting the wait time from the error message.
        Retries the request after the specified wait time.
        """
        # Extract wait time from the error message, default to 60 seconds if not found
        delay = int(re.search(r'\d+', str(e)).group()) if re.search(r'\d+', str(e)) else 60
        print(f"Rate limit exceeded. Waiting for {delay} seconds...")
        time.sleep(delay)
        # Increase request delay slightly to prevent repeated rate limit errors
        self.request_delay = min(self.request_delay * 2, 60)  # Exponential backoff with a max of 60 seconds

    def analyze_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity  # Returns a polarity score (-1 to 1)

    def analyze_comments_sentiment(self, submission, max_comments=10):
        total_sentiment = 0
        comment_count = 0

        submission.comments.replace_more(limit=0)
        for comment in submission.comments[:max_comments]:
            if comment.body:  # Check if comment has content
                comment_sentiment = self.analyze_sentiment(comment.body)
                total_sentiment += comment_sentiment
                comment_count += 1
        
        # Average sentiment for comments, or return 0 if there are no comments
        return total_sentiment / comment_count if comment_count > 0 else 0

    def collect_and_save_sentiment_data(self, prompts, limit=100):
        file_path = "/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/reddit_sentiment_data.csv"
        all_posts_data = []
        for prompt in prompts:
            print(f"\nProcessing prompt: {prompt}")
            subreddits = self.search_subreddits(prompt, num_subreddits=10)
            print(f"Subreddits found for '{prompt}': {subreddits}")
            for subreddit in subreddits:
                print(f"Scraping sentiment data from r/{subreddit}")
                subreddit_data = self.scrape_posts_with_sentiment(subreddit, limit=limit)
                all_posts_data.extend(subreddit_data)
        # Convert collected data to DataFrame
        new_df = pd.DataFrame(all_posts_data)
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path)
            # Convert timestamps to datetime for consistency
            existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'], errors='coerce')
            new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], errors='coerce')
            # Remove duplicates based on timestamp and URL
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp', 'url'], keep='first')
        else:
            combined_df = new_df
        combined_df.to_csv(file_path, index=False)
        print(f"Reddit sentiment data saved to {file_path}")