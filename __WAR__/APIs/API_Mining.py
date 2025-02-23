import requests
import pandas as pd
import os

class MiningDataCollector:
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_profitability_data(self):
        url = f"http://www.coinwarz.com/v1/api/profitability/?apikey={self.api_key}&algo=all"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Assuming the API response includes a "Data" field with profitability info
            return response.json().get("Data", [])
        else:
            print(f"Failed to fetch mining profitability data: {response.text}")
            return []

    def collect_and_save_profitability_data(self):
        path = "/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/mining_profitability_data.csv"
        profitability_data = self.fetch_profitability_data()

        if profitability_data:
            new_df = pd.DataFrame(profitability_data)

            if os.path.exists(path):
                existing_df = pd.read_csv(path)
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp'], keep='first')
            else:
                combined_df = new_df

            combined_df.to_csv(path, index=False)
            print(f"Mining profitability data saved to {path}")
        else:
            print("No profitability data available to save.")