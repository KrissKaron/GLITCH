import pandas as pd
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from datetime import timedelta
from __path__ import *

# Define file paths
PATH_PIVOT_PERIODS = f'{PATH_CSV}/PIVOT_PERIODS_1m.csv'
PATH_NEWS_IMPACT = f'{PATH_CSV}/NEWS_IMPACT.csv'

# Load the data with timezone consistency and reset index
pivots_df = pd.read_csv(PATH_PIVOT_PERIODS, parse_dates=['buy_time', 'sell_time'])
news_df = pd.read_csv(PATH_NEWS_IMPACT, parse_dates=['news_headline_publication_timestamp', 'insignificance_timestamp'])
news_df['impact_normalized'] = news_df['impact'] / news_df['impact'].max()

# Ensure timestamps are timezone-naive for comparison
pivots_df['buy_time'] = pivots_df['buy_time'].dt.tz_localize(None)
pivots_df['sell_time'] = pivots_df['sell_time'].dt.tz_localize(None)
news_df['news_headline_publication_timestamp'] = news_df['news_headline_publication_timestamp'].dt.tz_localize(None)
news_df['insignificance_timestamp'] = news_df['insignificance_timestamp'].dt.tz_localize(None)

def find_closest_timestamp(news_time):
    """Find the closest pivot timestamp to a given news time."""
    all_pivot_times = pd.concat([pivots_df['buy_time'], pivots_df['sell_time']]).sort_values().reset_index(drop=True)

    # Convert to datetime to avoid dtype issues
    news_time = pd.to_datetime(news_time)
    all_pivot_times = pd.to_datetime(all_pivot_times)

    # Find the closest time by index
    closest_time = all_pivot_times.iloc[(all_pivot_times - news_time).abs().idxmin()]
    return closest_time

# Custom Reinforcement Learning Environment
class HarveySpecter(gym.Env):
    def __init__(self):
        super(HarveySpecter, self).__init__()
        # Define action space (predicting pivot time within 200-minute window)
        self.action_space = spaces.Box(low=np.array([0.0]), high=np.array([200.0]), dtype=np.float32)
        # Define state space: [impact score, time diff ratio, pivot period normalization]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(3,), dtype=np.float32  # [impact, time_diff_ratio, normalized_period]
        )
        self.current_index = 0
        self.state = None

    def reset(self, seed=None, options=None):
        """Reset environment and return initial state."""
        if len(news_df) == 0:
            raise ValueError("The news data is empty. Ensure data is loaded properly.")
        self.current_index = random.randint(0, len(news_df) - 1)
        self.state = self._get_state()
        return self.state, {}

    def _get_state(self):
        """Retrieve the current state based on news impact and pivot periods."""
        if self.current_index >= len(news_df):
            self.current_index = len(news_df) - 1 
        news_row = news_df.iloc[self.current_index]
        closest_pivot_time = find_closest_timestamp(news_row['news_headline_publication_timestamp'])

        # Find period minutes for the closest pivot
        pivot_row = pivots_df[
            (pivots_df['buy_time'] == closest_pivot_time) | (pivots_df['sell_time'] == closest_pivot_time)
        ]

        if pivot_row.empty:
            pivot_period = 0
        else:
            pivot_period = pivot_row['period_minutes'].values[0]

        # Calculate features
        time_diff = abs((closest_pivot_time - news_row['news_headline_publication_timestamp']).total_seconds()) / 60
        impact = news_row['impact']
        normalized_period = pivot_period / 1440  # Normalize period by 1 day (1440 minutes)

        return np.array([
            impact / 100,  # Normalize impact score (assuming 0-100 scale)
            time_diff / 1440,  # Normalize time difference by 1 day
            normalized_period
        ], dtype=np.float32)

    def step(self, action):
        """Take an action and return the next state, reward, done, truncated, and info."""
        if self.current_index >= len(news_df):
            done = True
            truncated = False
            return self.state, 0.0, done, truncated, {}
        news_row = news_df.iloc[self.current_index]
        predicted_pivot_time = news_row['news_headline_publication_timestamp'] + timedelta(minutes=int(action[0]))
        closest_pivot_time = find_closest_timestamp(news_row['news_headline_publication_timestamp'])

        # Calculate actual pivot time difference
        actual_time_diff = abs((closest_pivot_time - predicted_pivot_time).total_seconds()) / 60

        # Instead of only penalizing for time difference, reward based on closeness
        #reward = max(0, 100 - actual_time_diff)        # Worked better
        reward = np.exp(-actual_time_diff / 50) * 100   # Exponential decay function
        self.current_index += 1
        done = self.current_index >= len(news_df)
        truncated = False
        return self._get_state(), reward, done, truncated, {}

    def render(self, mode='human'):
        print(f"State: {self.state}")