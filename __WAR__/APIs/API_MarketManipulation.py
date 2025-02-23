import requests
import pandas as pd
import os

class WhaleTrackingCollector:
    def __init__(self, jwt_token):
        self.jwt_token = jwt_token

    def fetch_on_chain_data(self, asset="bitcoin"):
        url = "https://api.santiment.net/graphql"
        headers = {"Authorization": f"Apikey {self.jwt_token}"}
        
        # GraphQL query for multiple metrics with different intervals
        query = """
        query {
            whale_transaction_count_100k_usd_to_inf: getMetric(metric: "whale_transaction_count_100k_usd_to_inf") {
                timeseriesData(
                    slug: "bitcoin"
                    from: "2022-11-08T00:00:00Z"
                    to: "2024-10-08T00:00:00Z"
                    interval: "6h"
                ) {
                    datetime
                    value
                }
            }
            whale_transaction_count_1m_usd_to_inf: getMetric(metric: "whale_transaction_count_1m_usd_to_inf") {
                timeseriesData(
                    slug: "bitcoin"
                    from: "2022-11-08T00:00:00Z"
                    to: "2024-10-08T00:00:00Z"
                    interval: "6h"
                ) {
                    datetime
                    value
                }
            }
        }
        """
        
        response = requests.post(url, headers=headers, json={'query': query})
        
        if response.status_code == 200:
            json_data = response.json()
            # Extract data for each metric and save to a CSV
            data = {}
            for metric, metric_data in json_data.get('data', {}).items():
                timeseries = metric_data.get('timeseriesData', [])
                data[metric] = timeseries

            return data  # Return dictionary of all metrics with their timeseries data
        else:
            print(f"Failed to fetch on-chain data: {response.text}")
            return {}

    def collect_and_save_on_chain_data(self, asset="bitcoin"):
        data = self.fetch_on_chain_data(asset=asset)

        for metric, timeseries_data in data.items():
            if timeseries_data:
                file_name = f"/home/krisskaron/GLITCH_1.21.4/__WAR__/csv/{metric}_data.csv"
                new_df = pd.DataFrame(timeseries_data)

                if os.path.exists(file_name):
                    existing_df = pd.read_csv(file_name)
                    combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp'], keep='first')
                else:
                    combined_df = new_df

                combined_df.to_csv(file_name, index=False)
                print(f"{metric} data saved to {file_name}")
            else:
                print(f"No data available for {metric}")