import pandas as pd
import numpy as np
from datetime import datetime
from __path__ import *

class Impactor:
    def __init__(self, input_file, output_file):
        """
        Initialize the Impactor class with input and output file paths.
        
        Args:
        - input_file (str): Path to the news CSV file.
        - output_file (str): Path to save the calculated news impact CSV.
        """
        self.input_file = input_file
        self.output_file = output_file
        self.df = None

    def load_data(self):
        """Loads the news data from the CSV file."""
        try:
            self.df = pd.read_csv(self.input_file, parse_dates=['published_at'])
            print(f"Successfully loaded data from {self.input_file}")
        except FileNotFoundError:
            print(f"Error: The file {self.input_file} was not found.")

    def calculate_impact(self, decay_factor=0.01):
        """
        Calculate news impact, insignificance timestamp, and period in minutes.

        Args:
        - decay_factor (float): Rate of decay for news impact.

        Returns:
        - pd.DataFrame: DataFrame containing assessed_news_headline_id, impact, 
                        news_headline_publication_timestamp, insignificance_timestamp, period_minutes.
        """
        EPSILON = 1e-6
        impact_data = []
        for _, row in self.df.iterrows():
            safe_initial_impact = max(row['importance_score'], EPSILON)
            assessed_id = row['title'][:15]  # First 15 characters of the title
            publication_time = row['published_at']

            # Calculate the insignificance timestamp (when impact falls below 10)
            time_to_insignificance = int(np.log(10 / safe_initial_impact) / -decay_factor)
            insignificance_time = publication_time + pd.Timedelta(minutes=time_to_insignificance)

            # Calculate the period in minutes
            period_minutes = (insignificance_time - publication_time).total_seconds() / 60

            impact_data.append({
                'assessed_news_headline_id': assessed_id,
                'impact': safe_initial_impact,
                'news_headline_publication_timestamp': publication_time,
                'insignificance_timestamp': insignificance_time,
                'period_minutes': period_minutes
            })
        return pd.DataFrame(impact_data)

    def remove_low_impact(self, impact_df):
        """Removes rows where the impact is below 10."""
        impact_df = impact_df[impact_df['impact'] >= 10]
        return impact_df

    def save_impact_to_csv(self, impact_df):
        """Saves the calculated impact data to the output CSV file."""
        impact_df.to_csv(self.output_file, index=False)
        print(f"Impact data saved to {self.output_file}")

    def run(self):
        """Executes the full pipeline: loading data, calculating impact, filtering, and saving."""
        self.load_data()
        impact_df = self.calculate_impact()
        impact_df = self.remove_low_impact(impact_df)
        self.save_impact_to_csv(impact_df)
        return impact_df
