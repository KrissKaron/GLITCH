import pandas as pd
import matplotlib.pyplot as plt

class BCKTST_historical:
    def __init__(self, file_path, initial_balance=1000, transaction_fee=0.001):
        """
        Initialize the backtesting class.

        Parameters:
        - file_path (str): Path to the CSV file containing pivot signals.
        - initial_balance (float): Starting balance for the portfolio.
        - transaction_fee (float): Transaction fee per trade (default 0.1%).
        """
        self.file_path = file_path
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.df = None
        self.cash = initial_balance
        self.holdings = 0
        self.portfolio_values = []
        self.timestamps = []

    def load_data(self):
        """Load the CSV file and preprocess the data."""
        self.df = pd.read_csv(self.file_path)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        print(f"Loaded {len(self.df)} rows from {self.file_path}")

    def run_backtest(self):
        """Execute the backtest simulation."""
        for _, row in self.df.iterrows():
            price = row['price']
            signal = row['signal']
            timestamp = row['timestamp']

            if signal == "buy" and self.cash > 0:
                self.holdings = self.cash / price  # Buy with all available cash
                self.holdings -= self.holdings * self.transaction_fee  # Apply fee
                self.cash = 0  # Cash is fully used

            elif signal == "sell" and self.holdings > 0:
                self.cash = self.holdings * price  # Sell all holdings
                self.cash -= self.cash * self.transaction_fee  # Apply fee
                self.holdings = 0  # No holdings left

            # Track portfolio value
            portfolio_value = self.cash + (self.holdings * price)
            self.portfolio_values.append(portfolio_value)
            self.timestamps.append(timestamp)

    def plot_results(self):
        """Plot the portfolio value over time."""
        plt.figure(figsize=(12, 6))
        plt.plot(self.timestamps, self.portfolio_values, label="Portfolio Value", color="blue")
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Time")
        plt.ylabel("Portfolio Value")
        plt.legend()
        plt.grid(True)
        plt.show()

    def print_summary(self):
        """Print a summary of the backtest results."""
        final_value = self.portfolio_values[-1]
        total_return = ((final_value - self.initial_balance) / self.initial_balance) * 100
        print(f"Final Portfolio Value: ${final_value:.2f}")
        print(f"Total Return: {total_return:.2f}%")

    def run(self):
        """Run the full backtesting process."""
        self.load_data()
        self.run_backtest()
        self.plot_results()
        self.print_summary()

import matplotlib.dates as mdates


class BCKTST_estimated:
    def __init__(self, news_file_path, bcktst_file_path, initial_balance=1000, transaction_fee=0.001):
        """
        Initialize the backtesting class.

        Parameters:
        - news_file_path (str): Path to the CSV file containing news signals.
        - bcktst_file_path (str): Path to the CSV file containing historical price data.
        - initial_balance (float): Starting balance for the portfolio.
        - transaction_fee (float): Transaction fee per trade (default 0.1%).
        """
        self.news_file_path = news_file_path
        self.bcktst_file_path = bcktst_file_path
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.df_news = None
        self.df_prices = None
        self.cash = initial_balance
        self.holdings = 0
        self.portfolio_values = []
        self.timestamps = []
        self.buy_times = []
        self.sell_times = []
        self.buy_prices = []
        self.sell_prices = []

    def load_data(self):
        """Load the CSV files and preprocess the data."""
        self.df_news = pd.read_csv(self.news_file_path, parse_dates=['news_headline_publication_timestamp', 'insignificance_timestamp'])
        self.df_news.sort_values(by='news_headline_publication_timestamp', inplace=True)
        print(f"Loaded {len(self.df_news)} rows from {self.news_file_path}")

        self.df_prices = pd.read_csv(self.bcktst_file_path, parse_dates=['timestamp'])
        self.df_prices.set_index('timestamp', inplace=True)
        print(f"Loaded {len(self.df_prices)} rows from {self.bcktst_file_path}")

    def run_backtest(self):
        """Execute the backtest simulation with adjusted buy/sell logic."""
        last_sell_time = None  # Track last sell time to ensure non-overlapping trades
        current_buy_time = None
        current_sell_time = None
        first_trade = True

        for _, row in self.df_news.iterrows():
            buy_time = row['news_headline_publication_timestamp']
            sell_time = row['insignificance_timestamp']
            impact = row['impact']

            # If this is the first trade or a new valid buy opportunity appears
            if first_trade or (buy_time > last_sell_time):
                if not first_trade:
                    # Perform sell before moving to next buy
                    self.execute_trade(current_sell_time, impact, buy=False)

                # Start a new trade
                current_buy_time = buy_time
                current_sell_time = sell_time
                first_trade = False  # Mark that we have entered a trade

                # Execute buy
                self.execute_trade(current_buy_time, impact, buy=True)
            
            else:
                # Extend the sell time if the news is still within the active trade
                if sell_time > current_sell_time:
                    current_sell_time = sell_time

            # Update last sell time when closing a trade
            last_sell_time = current_sell_time

        # Ensure final trade is closed
        if not first_trade:
            self.execute_trade(current_sell_time, impact, buy=False)

    def execute_trade(self, timestamp, impact, buy=False):
        """Execute a buy or sell trade."""
        # Ensure the index is a DatetimeIndex
        self.df_prices.index = pd.to_datetime(self.df_prices.index)

        # Convert timestamps to Unix timestamps for numeric comparison
        timestamp_unix = timestamp.timestamp()
        prices_unix = self.df_prices.index.astype('int64') // 10**9  # Convert to seconds

        # Find the closest price using absolute time difference
        closest_idx = (prices_unix - timestamp_unix).argsort()[0]
        closest_price_row = self.df_prices.iloc[closest_idx]

        # Get the actual price
        price = closest_price_row['close'] if not closest_price_row.empty else impact

        if buy and self.cash > 0:
            self.holdings = self.cash / price  # Buy with all available cash
            self.holdings -= self.holdings * self.transaction_fee  # Apply fee
            self.cash = 0  # Cash is fully used
            self.timestamps.append(timestamp)
            self.portfolio_values.append(self.holdings * price)  # Portfolio value at buy
            self.buy_times.append(timestamp)
            self.buy_prices.append(price)

        elif not buy and self.holdings > 0:
            self.cash = self.holdings * price  # Sell all holdings
            self.cash -= self.cash * self.transaction_fee  # Apply fee
            self.holdings = 0  # No holdings left
            self.timestamps.append(timestamp)
            self.portfolio_values.append(self.cash)  # Portfolio value at sell
            self.sell_times.append(timestamp)
            self.sell_prices.append(price)

    def plot_results(self):
        """Plot the portfolio value over time."""
        plt.figure(figsize=(30, 20))
        plt.plot(self.timestamps, self.portfolio_values, label="Portfolio Value", color="blue")
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Time")
        plt.ylabel("Portfolio Value")
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_signals(self):
        """Plot price data along with detected buy/sell signals from NEWS_PERIODS.csv."""
        plt.figure(figsize=(30, 20))

        # Plot the actual crypto price data from bcktst.csv
        plt.plot(self.df_prices['timestamp'], self.df_prices['close'], label="Close Price", color="blue", alpha=0.6)

        # Filter buy (news_headline_publication_timestamp) and sell (insignificance_timestamp) signals
        buy_signals = self.df_news[['news_headline_publication_timestamp', 'impact']].rename(
            columns={'news_headline_publication_timestamp': 'timestamp', 'impact': 'price'}
        )
        sell_signals = self.df_news[['insignificance_timestamp', 'impact']].rename(
            columns={'insignificance_timestamp': 'timestamp', 'impact': 'price'}
        )

        # Plot Buy signals
        plt.scatter(buy_signals['timestamp'], buy_signals['price'], color='green', label='Buy (News Event)', marker='^', s=150)

        # Plot Sell signals
        plt.scatter(sell_signals['timestamp'], sell_signals['price'], color='red', label='Sell (News Impact Decay)', marker='v', s=150)

        # Formatting
        plt.title("News-Based Buy/Sell Signals on Crypto Price Data")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)

        # Improve x-axis readability
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

        plt.show()

    def print_summary(self):
        """Print a summary of the backtest results."""
        if not self.portfolio_values:
            print("No trades were executed.")
            return
        final_value = self.portfolio_values[-1]
        total_return = ((final_value - self.initial_balance) / self.initial_balance) * 100
        print(f"Final Portfolio Value: ${final_value:.2f}")
        print(f"Total Return: {total_return:.2f}%")

    def run(self):
        """Run the full backtesting process."""
        self.load_data()
        self.run_backtest()
        self.plot_results()
        self.plot_signals()
        self.print_summary()


