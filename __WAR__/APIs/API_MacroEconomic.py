# Tracking interest rate/inflation (that impact BTC directly)
import requests
import pandas as pd
from textblob import TextBlob
import os

class EconomicDataCollector:
    def __init__(self, api_key, ticker="SPY"):
        self.api_key = api_key
        self.ticker = ticker

    def fetch_economic_news(self, limit=50):
        url = f"https://api.polygon.io/v2/reference/news"
        params = {
            'apiKey': self.api_key,
            'ticker': self.ticker,
            'limit': limit
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            print(f"Failed to fetch economic news: {response.text}")
            return []

    def analyze_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def collect_and_save_economic_news(self, limit=50):
        path = "/Users/iliemoromete/Desktop/GLITCH_1.21.4/__WAR__/csv/interest_rate.csv"
        articles = self.fetch_economic_news(limit=limit)

        data = []
        for article in articles:
            full_text = f"{article['title']} {article.get('description', '')}"
            sentiment_score = self.analyze_sentiment(full_text)
            data.append({
                'title': article['title'],
                'description': article.get('description', ''),
                'url': article['article_url'],
                'published_at': article['published_utc'],
                'sentiment_score': sentiment_score
            })

        new_df = pd.DataFrame(data)

        if os.path.exists(path):
            existing_df = pd.read_csv(path)
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'url'], keep='first')
        else:
            combined_df = new_df

        combined_df.to_csv(path, index=False)
        print(f"Interest rate data saved to {path}")

