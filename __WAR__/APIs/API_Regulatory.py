import requests
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import os

class API_Regulatory:
    def __init__(self, api_key, query='regulation', language='en'):
        self.api_key = api_key
        self.query = query
        self.language = language

    def fetch_regulatory_news(self, days=30):
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        url = f"https://cryptopanic.com/api/v1/posts/"
        params = {
            'auth_token': self.api_key,
            'filter': self.query,
            'kind': 'news',
            'public': 'true',
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get('results', [])
            print(f"Fetched {len(articles)} articles.")
            return articles
        else:
            print(f"Failed to fetch regulatory news: {response.text}")
            return []

    def analyze_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def collect_and_save_regulatory_news(self, days=30):
        path = "/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/regulatory_news.csv"
        articles = self.fetch_regulatory_news(days=days)

        data = []
        for article in articles:
            full_text = f"{article['title']} {article.get('description', '')}"
            sentiment_score = self.analyze_sentiment(full_text)
            data.append({
                'title': article['title'],
                'description': article.get('description', ''),
                'url': article['url'],
                'published_at': article['published_at'],
                'sentiment_score': sentiment_score
            })

        new_df = pd.DataFrame(data)

        if os.path.exists(path):
            existing_df = pd.read_csv(path)
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'url'], keep='first')
        else:
            combined_df = new_df

        combined_df.to_csv(path, index=False)
        print(f"Regulatory news data saved to {path}")