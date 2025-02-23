import pandas as pd
import sys
import matplotlib.pyplot as plt
from __path__ import *
PATH_ROOT                   = f'{path_root}/GLITCH_1.21.4/__WAR__'
PATH_NEWS                   = f'{PATH_WAR}/NEWS.csv'

input_pivots_path           = f'{PATH_CSV}/PIVOTS_1m.csv'
output_periods_path         = f'{PATH_CSV}/PIVOT_PERIODS_1m.csv'
input_news_file             = f"{PATH_WAR}/NEWS.csv"
output_impact_file          = f"{PATH_CSV}/NEWS_IMPACT.csv"

from AMPLITUDE import *
from _DATA import *
import numpy as np
from datetime import datetime
import asyncio
from _pivot import Pivot
from _deltaT import deltaTextractor
from _impact import Impactor

async def run_pivot_detection(klines_file):
    klines_df = pd.read_csv(klines_file)
    pivot_detector = Pivot(klines_df, interval='1m', window_size=5, significance_threshold=0.001)
    await asyncio.get_event_loop().run_in_executor(None, pivot_detector.run)

async def run_deltaT_extraction(input_path, output_path):
    analyzer = deltaTextractor(input_path, output_path)
    await asyncio.get_event_loop().run_in_executor(None, analyzer.run)

async def run_news_impact(input_file, output_file):
    impactor = Impactor(input_file, output_file)
    await asyncio.get_event_loop().run_in_executor(None, impactor.load_data)
    impact_df = await asyncio.get_event_loop().run_in_executor(None, impactor.calculate_impact)
    impact_df = impactor.remove_low_impact(impact_df)
    await asyncio.get_event_loop().run_in_executor(None, impactor.save_impact_to_csv, impact_df)
    print(impact_df.head())

async def main():
    while True:
        tasks = [
            fetch_general_news(),                                                   #1
            fetch_regulatory_news(),                                                #2
            fetch_whale_alerts(),                                                   #3
            fetch_economic_news(),                                                  #4
            fetch_on_chain_data(),                                                  #5
            fetch_mining_data(),                                                    #6
            fetch_binance_klines(),                                                 #7
            excavate_score_compact(),                                               #8
            run_pivot_detection(PATH_KLINES),                                       #9
            run_deltaT_extraction(input_pivots_path,output_periods_path),           #10
            run_news_impact(input_news_file,output_impact_file)                     #11
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {idx+1} failed: {result}")
            else:
                print(f"Task {idx+1} completed successfully.")
        print("Waiting for next run...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())