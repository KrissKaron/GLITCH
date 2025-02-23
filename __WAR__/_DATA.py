import asyncio
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime
from AMPLITUDE import *
import sys, os
import logging
from __path__ import *
logging.basicConfig(filename=f'{PATH_GLITCH}/__WAR__/logs/scraper.log',
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

PATH_ROOT = f'{PATH_GLITCH}/__WAR__'

sys.path.append(f'{PATH_ROOT}/APIs')
sys.path.append(f'{PATH_ROOT}/class')
from MarketDataCollector import MDC
# Importing API modules
from API_Sentiment import RedditSentimentScraper
from API_Newsapi import API_Newsapi
from API_Regulatory import API_Regulatory
from API_Whales import WhaleAlertCollector
from API_MacroEconomic import EconomicDataCollector
from API_MarketManipulation import WhaleTrackingCollector
from API_Mining import MiningDataCollector
from API_Binance import API_Binance

# Import API keys
from __keys__ import (
    API_REDDIT_CLIENTID, API_REDDIT_CLIENTSECRET, API_REDDIT_CLIENTUSERAGENT,
    API_NEWSAPI, API_CRYPTOPANIC, API_WHALES, API_POLYGON, API_SANTIMENT,
    API_COINWARZ, API_BINANCE_PUBLIC, API_BINANCE_PRIVATE
)

# Function to run synchronous API calls in an executor
def run_sync_task(task, *args, **kwargs):
    return task(*args, **kwargs)

async def fetch_reddit_sentiment():
    try:
        prompts = [
            "Bitcoin", "BTC", "BTC price", "Bitcoin price", "BTC adoption", "Bitcoin adoption",
            "BTC ta", "Bitcoin technical analysis", "Bitcoin mining", "BTC news", "Bitcoin news",
            "halving", "BTC halving", "Bitcoin halving", "BTC bull", "BTC bear", "Bitcoin bear",
            "Bitcoin bull"
        ]
        scraper = RedditSentimentScraper(API_REDDIT_CLIENTID, API_REDDIT_CLIENTSECRET, API_REDDIT_CLIENTUSERAGENT)
        return await asyncio.get_event_loop().run_in_executor(None, scraper.collect_and_save_sentiment_data, prompts, 100)
    except Exception as e:
        print(f"Error fetching Reddit sentiment: {e}")
        return None

async def fetch_whale_alerts():
    whale_alert = WhaleAlertCollector(API_WHALES)
    return await asyncio.get_event_loop().run_in_executor(None, whale_alert.collect_and_save_transactions, "btc", 500000)

async def fetch_regulatory_news():
    try:
        regulatory_news = API_Regulatory(API_CRYPTOPANIC)
        await asyncio.get_event_loop().run_in_executor(None, regulatory_news.collect_and_save_regulatory_news, 30)
        logging.info("Regulatory news data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching regulatory news: {e}")

async def fetch_general_news():
    try:
        news_api = API_Newsapi(API_NEWSAPI)
        await asyncio.get_event_loop().run_in_executor(None, news_api.collect_news_data, 30)
        logging.info("General news data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching general news: {e}")

async def fetch_mining_data():
    try:
        mining_data_collector = MiningDataCollector(api_key=API_COINWARZ)
        await asyncio.get_event_loop().run_in_executor(None, mining_data_collector.collect_and_save_profitability_data)
        logging.info("Mining data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching mining data: {e}")

async def fetch_on_chain_data():
    try:
        whale_tracking_collector = WhaleTrackingCollector(jwt_token=API_SANTIMENT)
        await asyncio.get_event_loop().run_in_executor(None, whale_tracking_collector.collect_and_save_on_chain_data, "bitcoin")
        logging.info("On-chain data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching on-chain data: {e}")

async def fetch_economic_news():
    try:
        economic_data_collector = EconomicDataCollector(api_key=API_POLYGON)
        await asyncio.get_event_loop().run_in_executor(None, economic_data_collector.collect_and_save_economic_news, 50)
        logging.info("Economic news data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching economic news: {e}")

async def fetch_binance_klines():
    try:
        file_path = f"{PATH_ROOT}/GLITCH_1.21.4/__WAR__/csv/BTCUSDC_klines.csv"

        # Determine dynamic start date based on existing data
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path)
            if 'timestamp' in existing_df.columns and not existing_df.empty:
                latest_timestamp = pd.to_datetime(existing_df['timestamp'].max())
                start_date = int(latest_timestamp.timestamp() * 1000)
            else:
                start_date = int((datetime.now() - timedelta(days=5)).timestamp() * 1000)
        else:
            start_date = int((datetime.now() - timedelta(days=5)).timestamp() * 1000)
        end_date = int((datetime.now()).timestamp() * 1000)
        _api_binance_ = API_Binance(API_BINANCE_PUBLIC, API_BINANCE_PRIVATE)
        client, server_timestamp, acc_snapshot = _api_binance_.execute()
        print(f"Fetching Binance Klines from {datetime.utcfromtimestamp(start_date / 1000)} to {datetime.utcfromtimestamp(end_date / 1000)}")
        mdc = MDC(client, '1m', start_date, end_date)
        result = await asyncio.get_event_loop().run_in_executor(None, mdc.get_historical_data)
        if result is None or result.empty:
            logging.warning("No new Binance Klines data available.")
        else:
            logging.info("Binance Klines data fetched and saved successfully.")
    except Exception as e:
        logging.error(f"Error fetching Binance klines data: {e}")
        print(f"Error: {e}")

async def excavate_score_compact():
    extractor = CSVExcavator(PATH_ROOT)
    scorer = NewsScorer()

    # Extract data asynchronously with error handling
    general_news_df = await asyncio.get_event_loop().run_in_executor(None, extractor.extract_general_news)
    interest_rate_df = await asyncio.get_event_loop().run_in_executor(None, extractor.extract_interest_rate_news)
    regulatory_news_df = await asyncio.get_event_loop().run_in_executor(None, extractor.extract_regulatory_news)
    whale_transactions_df = await asyncio.get_event_loop().run_in_executor(None, extractor.extract_whale_transactions)

    # Ensure data is not None; replace with an empty DataFrame if necessary
    general_news_df = general_news_df if general_news_df is not None else pd.DataFrame(columns=['title', 'description', 'content', 'published_at'])
    interest_rate_df = interest_rate_df if interest_rate_df is not None else pd.DataFrame(columns=['title', 'description', 'published_at'])
    regulatory_news_df = regulatory_news_df if regulatory_news_df is not None else pd.DataFrame(columns=['title', 'description', 'published_at'])
    whale_transactions_df = whale_transactions_df if whale_transactions_df is not None else pd.DataFrame(columns=['datetime', 'value'])

    # Score the news asynchronously
    scored_general_news = await asyncio.get_event_loop().run_in_executor(None, scorer.score_general_news, general_news_df)
    scored_interest_rate = await asyncio.get_event_loop().run_in_executor(None, scorer.score_interest_rate_news, interest_rate_df)
    scored_regulatory_news = await asyncio.get_event_loop().run_in_executor(None, scorer.score_regulatory_news, regulatory_news_df)
    scored_whale_transactions = await asyncio.get_event_loop().run_in_executor(None, scorer.score_whale_transactions, whale_transactions_df)

    # Instantiate the compacter class AFTER scoring is done
    compacter = CSVCompacter(scored_general_news, scored_interest_rate, scored_regulatory_news, scored_whale_transactions)
    await asyncio.get_event_loop().run_in_executor(None, compacter.save_to_csv)
    print("Data successfully compacted and saved.")
