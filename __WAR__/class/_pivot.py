import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from __path__ import *

class Pivot:
    def __init__(self, df, interval, window_size=5, significance_threshold=0.001):
        """
        Initialize the pivot detection algorithm.

        Parameters:
        - df: DataFrame containing price data with 'timestamp' and 'close' columns.
        - interval: The time interval (e.g., '1m', '15m', etc.).
        - window_size: Number of surrounding values to check for local extrema.
        - significance_threshold: Minimum relative change to consider as a pivot point.
        """
        self.df = df.copy()
        self.interval = interval
        self.window_size = window_size
        self.significance_threshold = significance_threshold
        self.pivots = None
        self.signals = None

        # Ensure timestamp is in datetime format
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

        # Convert pivot column to object type to handle mixed values
        self.df['pivot'] = np.nan
        self.df['pivot'] = self.df['pivot'].astype('object')

    def detect_pivots(self):
        """Detect local minima and maxima using a rolling window."""

        # Ensure pivot column is of object type to handle string values
        self.df['pivot'] = None
        self.df['pivot'] = self.df['pivot'].astype('object')

        # Calculate the percentage change before applying the function
        self.df['price_change'] = self.df['close'].pct_change().abs()

        # Identify local minima and maxima
        self.df['local_min'] = self.df['close'].rolling(window=self.window_size, center=True).apply(
            lambda x: x[self.window_size // 2] if x[self.window_size // 2] == np.min(x) else np.nan,
            raw=True
        )

        self.df['local_max'] = self.df['close'].rolling(window=self.window_size, center=True).apply(
            lambda x: x[self.window_size // 2] if x[self.window_size // 2] == np.max(x) else np.nan,
            raw=True
        )

        # Apply function row-wise to classify pivot points
        def classify_pivot(row):
            if pd.notna(row['local_min']) and row['price_change'] > self.significance_threshold:
                return 'min'
            elif pd.notna(row['local_max']) and row['price_change'] > self.significance_threshold:
                return 'max'
            return None

        self.df['pivot'] = self.df.apply(classify_pivot, axis=1)

        # Drop rows where pivot is still None (no pivot identified)
        self.pivots = self.df.dropna(subset=['pivot'])

    def generate_signals(self):
        """Generate buy/sell signals based on pivot points."""
        self.signals = []
        last_signal = None

        for idx, row in self.pivots.iterrows():
            if row['pivot'] == 'min' and last_signal != 'buy':
                self.signals.append((row['timestamp'], row['close'], "buy"))
                last_signal = "buy"
            elif row['pivot'] == 'max' and last_signal != 'sell':
                self.signals.append((row['timestamp'], row['close'], "sell"))
                last_signal = "sell"
            else:
                self.signals.append((row['timestamp'], row['close'], "hold"))

    def save_to_csv(self):
        """Save the signals to a CSV file."""
        output_path = f'{PATH_GLITCH}/__WAR__/csv/PIVOTS_{self.interval}.csv'
        signals_df = pd.DataFrame(self.signals, columns=['timestamp', 'price', 'signal'])
        signals_df.to_csv(output_path, index=False)
        print(f"Pivot signals saved to {output_path}")

    def plot_signals(self):
        """Plot price data along with detected buy/sell signals."""
        plt.figure(figsize=(30, 20))
        plt.plot(self.df['timestamp'], self.df['close'], label="Close Price", color="blue")

        buy_signals = self.df[self.df['pivot'] == 'min']
        sell_signals = self.df[self.df['pivot'] == 'max']

        plt.scatter(buy_signals['timestamp'], buy_signals['close'], color='green', label='Buy (Local Minima)', marker='^')
        plt.scatter(sell_signals['timestamp'], sell_signals['close'], color='red', label='Sell (Local Maxima)', marker='v')

        plt.title("Local Minima and Maxima Detection")
        plt.xlabel("Time")
        plt.ylabel("Close Price")
        plt.legend()
        plt.grid(True)
        plt.show()

    def run(self):
        """Run the full pipeline."""
        self.detect_pivots()
        self.generate_signals()
        self.save_to_csv()
        #self.plot_signals()