import pandas as pd

class deltaTextractor:
    def __init__(self, input_file, output_file):
        """
        Initialize the PivotPeriodAnalyzer with input and output file paths.
        
        Args:
        - input_file (str): Path to the PIVOTS_1m.csv file.
        - output_file (str): Path to save the calculated pivot periods.
        """
        self.input_file = input_file
        self.output_file = output_file
        self.df = None
        self.periods = []

    def load_data(self):
        """Loads the CSV file and parses the timestamp column."""
        try:
            self.df = pd.read_csv(self.input_file, parse_dates=['timestamp'])
            print(f"Successfully loaded data from {self.input_file}")
        except FileNotFoundError:
            print(f"Error: The file {self.input_file} was not found.")
            self.df = None

    def calculate_periods(self):
        """Calculates the time difference between consecutive buy/sell signals."""
        if self.df is None:
            print("Data not loaded. Please check the file path.")
            return   
        buy_time = None
        for index, row in self.df.iterrows():
            if row['signal'] == 'buy':
                buy_time = row['timestamp']
            elif row['signal'] == 'sell' and buy_time is not None:
                sell_time = row['timestamp']
                period = (sell_time - buy_time).total_seconds() / 60  # Convert to minutes
                self.periods.append({
                    'index': len(self.periods),
                    'buy_time': buy_time,
                    'sell_time': sell_time,
                    'period_minutes': period
                })
                buy_time = None  # Reset buy time
        print(f"Calculated {len(self.periods)} periods.")

    def save_periods_to_csv(self):
        """Saves the calculated periods to the output CSV file."""
        if not self.periods:
            print("No periods calculated. Run 'calculate_periods()' first.")
            return
        periods_df = pd.DataFrame(self.periods)
        periods_df.to_csv(self.output_file, index=False)
        print(f"Periods saved successfully to {self.output_file}")

    def run(self):
        """Executes the entire process: loading data, calculating periods, and saving to CSV."""
        self.load_data()
        self.calculate_periods()
        self.save_periods_to_csv()
        return pd.DataFrame(self.periods)

