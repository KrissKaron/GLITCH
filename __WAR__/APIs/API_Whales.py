import requests
import pandas as pd
import os

class WhaleAlertCollector:
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_large_transactions(self, symbol="btc", min_value=1000000):
        url = f"https://api.whale-alert.io/v1/transactions"
        params = {
            'api_key': self.api_key,
            'symbol': symbol,
            'min_value': min_value
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('transactions', [])
        else:
            print(f"Failed to fetch whale transactions: {response.text}")
            return []

    def collect_and_save_transactions(self, symbol="btc", min_value=1000000):
        """
        Collect large transactions and append only new entries to the CSV file.
        
        Args:
        - symbol (str): Cryptocurrency symbol, default is "btc".
        - min_value (int): Minimum transaction value to fetch.
        """
        transactions = self.fetch_large_transactions(symbol=symbol, min_value=min_value)
        file_path = f"/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/{symbol}_large_transactions.csv"
        if transactions:
            data = []
            for tx in transactions:
                data.append({
                    'timestamp': tx['timestamp'],
                    'transaction_type': tx['transaction_type'],
                    'amount': tx['amount'],
                    'amount_usd': tx['amount_usd'],
                    'hash': tx['hash'],
                    'from_address': tx['from']['address'],
                    'from_owner': tx['from'].get('owner', ''),  
                    'to_address': tx['to']['address'],
                    'to_owner': tx['to'].get('owner', ''),  
                    'blockchain': tx['blockchain'],
                    'symbol': tx['symbol']
                })
            new_df = pd.DataFrame(data)

            # Check if file exists and load existing data
            if os.path.exists(file_path):
                existing_df = pd.read_csv(file_path)
                # Convert timestamp to avoid type mismatches
                existing_df['timestamp'] = pd.to_numeric(existing_df['timestamp'], errors='coerce')
                new_df['timestamp'] = pd.to_numeric(new_df['timestamp'], errors='coerce')
                # Identify new transactions
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp', 'hash'], keep='first')
                # Save only new unique transactions
                combined_df.to_csv(file_path, index=False)
                print(f"New transactions appended to {file_path}")
            else:
                # If file doesn't exist, create a new one
                new_df.to_csv(file_path, index=False)
                print(f"Transaction data saved to {file_path}")
        else:
            print("No new transactions available to save.")

