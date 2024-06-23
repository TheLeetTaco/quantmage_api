from dataclasses import dataclass
from typing import List, Any, Dict
from datetime import datetime
import concurrent.futures
import quantstats as qs
import pandas as pd
import numpy as np
import random
import json
import time

# Easter Egg
def magic_8_ball():
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes – definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    print("Will this Spell make money: ")
    # Fancy shaking effect with moving periods
    for _ in range(3):
        for i in range(4):
            print("Shaking", "." * i, " " * (2 - i), end="\r")
            time.sleep(0.25)
        for i in range(4):
            print("Shaking", "." * (2 - i), " " * i, end="\r")
            time.sleep(0.25)
    print(" " * 20, end="\r")  # Clear the line
    
    # Select a random response
    print(random.choice(responses))

@dataclass
class Allocation:
    """Used to store the allocation
    """
    ticker: str
    weight: float
    profit: float
    
@dataclass
class Info:
    """Used as a wrapper for each days information
    """
    date : int
    tickers: List[int]
    allocation: Allocation
    branches: List[int]
    profit: float

@dataclass
class Spell:
    """Main Datastorage for Quantmage

    NOTE: Any method using window_size will default to using the number_of_days if not supplied

    Returns:
        Quantmage Dataclass: Stores the API call
    """
    name: str 
    assets: List[str] 
    backtest_percent: List[float] 
    backtest_percent_yc_to: List[float] 
    dates: List[int] 
    formatted_dates: List[str] 
    allocation_history: List[List[Allocation]] 
    visited_leaves_history: List[List[int]] 
    daily_data: List[Info]
    # weekly_data: List[Info]
    # monthly_data: List[Info]
    # yearly_data: List[Info]
    number_of_days: int 
    days_traded_yearly = 252
    other_fields: Dict[str, Any] 

    @staticmethod
    def from_json(obj: json) -> 'Spell':
        """From JSON load into a Spell

        Args:
            obj (json): json output from 

        Returns:
            Spell: Spell Loaded into a Dataclass
        """
        _name = obj.get("spell_name")
        _backtest_percent = obj.get("value_history")
        _backtest_percent_yc_to = obj.get("value_history2")
        _assets = obj.get("assets")
        
        _branches = obj.get("visited_leaves_history")
        
        with open('dates.json', 'r') as file:
            raw_dates = json.load(file)["dates"]
        
        
        # Format dates from YYYYMMDD to YYYY-MM-DD
        _formatted_dates = [datetime.strptime(str(date), "%Y%m%d").strftime("%Y-%m-%d") for date in raw_dates]
        
        
        _allocation_history = [[Allocation(*allocation) for allocation in sublist] for sublist in obj.get("allocation_history")]
        # Selects the dates the algo uses
        spell_length = -len(_allocation_history)
        _dates = raw_dates[spell_length:]
        _number_of_days = len(_dates)
        # Mapping each allocation to the associated ticker from assets
        for day in _allocation_history:
            for allocation in day:
                allocation.ticker = _assets[allocation.ticker]
                
        _visited_leaves_history = obj.get("visited_leaves_history")
        
        _daily_data = []
        # Iterate over each day collecting info
        for index, date in enumerate(_dates):
            # Collect Daily Info
            profit = 0.0
            day_tickers = []
            for asset in _allocation_history[index]:
                profit += asset.profit
            _daily_data.append(Info(date=date, tickers=day_tickers, allocation=_allocation_history[index], branches=_branches[index], profit=profit))
        
        # Extract other fields
        known_fields = {"value_history", "dates", "allocation_history", "visited_leaves_history"}
        _other_fields = {k: v for k, v in obj.items() if k not in known_fields}
        
        return Spell(_name, _assets , _backtest_percent, _backtest_percent_yc_to, _dates, _formatted_dates, _allocation_history, _visited_leaves_history, _daily_data ,_number_of_days, _other_fields)

    @staticmethod
    def from_json_file(file_path: str) -> 'Spell':
        """From a Json file load it in to a Spell

        Args:
            file_path (str): Spell Json

        Returns:
            Spell: Spell Dataclass
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return Spell.from_json(data)
    
    def rolling_window(self, data, window_size):
        """Helper function to create a rolling window view of the data."""
        shape = data.shape[:-1] + (data.shape[-1] - window_size + 1, window_size)
        strides = data.strides + (data.strides[-1],)
        return np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)
    
    def prep_data(self, data) -> 'pd.Dataframe':
        """Used to setup data for use in quantstats.stats

        Args:
            data (List): List of Deltas

        Returns:
            pd.Dataframe: Dataframe to be used in quantstats.stats
        """
        returns_df = pd.DataFrame(data, columns=['returns'])
        returns_df.index = pd.date_range(start=datetime.strptime(str(self.dates[0]), "%Y%m%d"), periods=len(data), freq='D')
        
        return returns_df
    
    def calculate_cagr(self, data: List=None) -> List[float]:
        """Calculate the rolling CAGR % based on backtest_percent for a given window size.

        Args:
            data (int): The data to calculate on

        Returns:
            List[float]: The CAGR % truncated to two decimal places.
        """
        data = data if data else self.backtest_percent
        
        returns_df = self.prep_data(data)
        cagr = qs.stats.cagr(pd.DataFrame(returns_df['returns']))
        
        return round(cagr["returns"]*100, 2)
    
    def calculate_kelly_criterion(self, data: List=None) -> List[float]:
        """Calculate the kelly criterion based on the data passed in.

        Args:
            data (int): The data to calculate on

        Returns:
            List[float]: The kelly criterion truncated to two decimal places.
        """
        data = data if data else self.backtest_percent
        
        returns_df = self.prep_data(data)
        kelly = qs.stats.kelly_criterion(pd.DataFrame(returns_df['returns']))
        
        return round(kelly["returns"]*100, 2)
    
if __name__ == "__main__":
    mixed = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\81e1430056f8e243f6ff97855738bdca.json")
    print(mixed.name)
    # enter = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\ba7158f9bf6d88ea87db0341f6c4a849.json")
    # print(enter.name)
    
    print(f"CAGR: {mixed.calculate_cagr()}%")
    print(f"Kelly Criterion: {mixed.calculate_kelly_criterion()}%")
   
    # magic_8_ball()
    