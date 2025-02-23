import requests
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import os

# General news
class API_Newsapi:
    def __init__(self, api_key, query='bitcoin', language='en'):
        self.api_key = api_key
        self.query = query
        self.language = language

    def fetch_news(self, from_date, to_date):
        url = f"https://newsapi.org/v2/everything"
        params = {
            'q': self.query,
            'language': self.language,
            'from': from_date,
            'to': to_date,
            'sortBy': 'publishedAt',
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get('articles', [])
            print(f"Fetched {len(articles)} articles.")
            return articles
        else:
            print(f"Failed to fetch news: {response.text}")
            return []

    def analyze_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def collect_news_data(self, days=30):
        path = "/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/general_news.csv"
        to_date = datetime.today()
        from_date = to_date - timedelta(days=days)
        from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        articles = self.fetch_news(from_date=from_date_str, to_date=to_date_str)

        data = []
        for article in articles:
            full_text = f"{article['title']} {article['description']} {article['content']}"
            sentiment_score = self.analyze_sentiment(full_text)
            data.append({
                'title': article['title'],
                'description': article['description'],
                'content': article['content'],
                'url': article['url'],
                'publishedAt': article['publishedAt'],
                'sentiment_score': sentiment_score
            })

        new_df = pd.DataFrame(data)

        if os.path.exists(path):
            existing_df = pd.read_csv(path)
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['title', 'url'], keep='first')
        else:
            combined_df = new_df

        combined_df.to_csv(path, index=False)
        print(f"General news data saved to {path}")
