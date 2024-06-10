from dataclasses import dataclass, field
from typing import List, Any, Dict
from datetime import datetime
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
class Quantmage_Data:
    spell_name: str = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    backtest_percent: List[float] = field(default_factory=list)
    backtest_percent_yc_to: List[float] = field(default_factory=list)
    dates: List[int] = field(default_factory=list)
    formatted_dates: List[str] = field(default_factory=list)
    allocation_history: List[List[Allocation]] = field(default_factory=list)
    visited_leaves_history: List[List[int]] = field(default_factory=list)
    length_of_backtest: int = field(default_factory=dict)
    other_fields: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_json(obj: Any) -> 'Quantmage_Data':
        _spell_name = obj.get("spell_name")
        _backtest_percent = obj.get("value_history")
        _backtest_percent_yc_to = obj.get("value_history2")
        _assets = obj.get("assets")
        
        with open('dates.json', 'r') as file:
            raw_dates = json.load(file)["dates"]
        # Selects the dates the algo uses
        _dates = raw_dates[raw_dates.index(max(obj.get("data_ranges"))):]
        
        # Format dates from YYYYMMDD to YYYY_MM_DD
        _formatted_dates = [datetime.strptime(str(date), "%Y%m%d").strftime("%Y_%m_%d") for date in raw_dates]
        
        _length_of_backtest = len(_dates)
        _allocation_history = [[Allocation(*allocation) for allocation in sublist] for sublist in obj.get("allocation_history")]
        # Mapping each allocation to the associated ticker from assets
        for day in _allocation_history:
            for allocation in day:
                allocation.ticker = _assets[allocation.ticker]
                
        _visited_leaves_history = obj.get("visited_leaves_history")
        
        # Extract other fields
        known_fields = {"value_history", "dates", "allocation_history", "visited_leaves_history"}
        _other_fields = {k: v for k, v in obj.items() if k not in known_fields}
        
        return Quantmage_Data(_spell_name, _assets , _backtest_percent, _backtest_percent_yc_to, _dates, _formatted_dates, _allocation_history, _visited_leaves_history, _length_of_backtest, _other_fields)

    @staticmethod
    def from_json_file(file_path: str) -> 'Quantmage_Data':
        with open(file_path, 'r') as file:
            data = json.load(file)
        return Quantmage_Data.from_json(data)
    
if __name__ == "__main__":
    data = Quantmage_Data.from_json_file("D:\\Git Repos\\quantmage_api\\81e1430056f8e243f6ff97855738bdca.json")
    