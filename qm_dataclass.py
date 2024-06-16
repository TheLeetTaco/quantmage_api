from dataclasses import dataclass
from typing import List, Any, Dict
from datetime import datetime
import numpy as np
import json

@dataclass
class Allocation:
    """Used to store the allocation
    """
    ticker: str
    weight: float
    profit: float
    
@dataclass
class Day_Info:
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
    daily_info: List[Day_Info] 
    number_of_days: int 
    other_fields: Dict[str, Any] 

    @staticmethod
    def from_json(obj: Any) -> 'Spell':
        _name = obj.get("spell_name")
        _backtest_percent = obj.get("value_history")
        _backtest_percent_yc_to = obj.get("value_history2")
        _assets = obj.get("assets")
        
        _branches = obj.get("visited_leaves_history")
        
        with open('dates.json', 'r') as file:
            raw_dates = json.load(file)["dates"]
        
        
        # Format dates from YYYYMMDD to YYYY_MM_DD
        _formatted_dates = [datetime.strptime(str(date), "%Y%m%d").strftime("%Y_%m_%d") for date in raw_dates]
        
        
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
        
        _daily_info = []
        # Iterate over each day collecting info
        for index, date in enumerate(_dates):
            # Collect Daily Info
            profit = 0.0
            day_tickers = []
            for asset in _allocation_history[index]:
                profit += asset.profit
            _daily_info.append(Day_Info(date=date, tickers=day_tickers, allocation=_allocation_history[index], branches=_branches[index], profit=profit))
        
        # Extract other fields
        known_fields = {"value_history", "dates", "allocation_history", "visited_leaves_history"}
        _other_fields = {k: v for k, v in obj.items() if k not in known_fields}
        
        return Spell(_name, _assets , _backtest_percent, _backtest_percent_yc_to, _dates, _formatted_dates, _allocation_history, _visited_leaves_history, _daily_info ,_number_of_days, _other_fields)

    @staticmethod
    def from_json_file(file_path: str) -> 'Spell':
        with open(file_path, 'r') as file:
            data = json.load(file)
        return Spell.from_json(data)
    
    def calc_corelation(self, other: 'Spell') -> Dict:
        """Handles calculating the correlations when comparing to another spell

        Args:
            other (Spell): Spell to compare to

        Returns:
            Dict: Returns correlation for base backtest and yc_to_backtest
        """
        backtest_len = -min(len(self.backtest_percent), len(other.backtest_percent))
        this_spell = self.backtest_percent[backtest_len:]
        other_spell = other.backtest_percent[backtest_len:]
        
        # Calculate and return the correlation coefficient
        correlation = round(np.corrcoef(this_spell, other_spell)[0, 1], 2)
        
        this_spell = self.backtest_percent_yc_to[backtest_len:]
        other_spell = other.backtest_percent_yc_to[backtest_len:]
        # Calculate and return the correlation coefficient
        yc_tocorrelation = round(np.corrcoef(this_spell, other_spell)[0, 1], 2)
        
        # yc_to correlation
        output = {"correlation": correlation,
                  "yc_to_correlation": yc_tocorrelation}
        return output
    
    def calculate_cagr(self) -> float:
        """Calculate the Compound Annual Growth Rate (CAGR) based on backtest_percent.

        Returns:
            float: The CAGR value truncated to two decimal places.
        """
        if len(self.backtest_percent) == 0:
            raise ValueError("The backtest_percent list is empty.")
        
        beginning_value = self.backtest_percent[0]
        ending_value = self.backtest_percent[-1]
        number_of_years = self.number_of_days / 252  # Assuming 252 trading days in a year
        
        cagr = (ending_value / beginning_value) ** (1 / number_of_years) - 1
        return round(cagr, 2)
        
    
if __name__ == "__main__":
    mixed = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\81e1430056f8e243f6ff97855738bdca.json")
    print(mixed.name)
    enter = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\ba7158f9bf6d88ea87db0341f6c4a849.json")
    print(enter.name)
    
    print(mixed.calc_corelation(enter))
    
    print(mixed.calculate_cagr())