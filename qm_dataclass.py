from dataclasses import dataclass, field
from typing import List, Any, Dict
import matplotlib.pyplot as plt
from datetime import datetime
import json


@dataclass
class Allocation:
    asset: int
    value1: float
    value2: float

@dataclass
class Quantmage_Data:
    value_history: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    allocation_history: List[List[Allocation]] = field(default_factory=list)
    visited_leaves_history: List[List[int]] = field(default_factory=list)
    length_of_backtest: int = field(default_factory=dict)
    other_fields: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_json(obj: Any) -> 'Quantmage_Data':
        _value_history = obj.get("value_history")
        
        # Format dates from YYYYMMDD to YYYY_MM_DD
        raw_dates = obj.get("dates", [])
        raw_dates = raw_dates[raw_dates.index(max(obj.get("data_ranges"))):]
        _dates = [datetime.strptime(str(date), "%Y%m%d").strftime("%Y_%m_%d") for date in raw_dates]
        
        _length_of_backtest = len(_dates)
        _allocation_history = [[Allocation(*allocation) for allocation in sublist] for sublist in obj.get("allocation_history", [])]
        _visited_leaves_history = obj.get("visited_leaves_history", [])
        
        # Extract other fields
        known_fields = {"value_history", "dates", "allocation_history", "visited_leaves_history"}
        _other_fields = {k: v for k, v in obj.items() if k not in known_fields}
        
        return Quantmage_Data(_value_history, _dates, _allocation_history, _visited_leaves_history, _length_of_backtest, _other_fields)

    @staticmethod
    def from_json_file(file_path: str) -> 'Quantmage_Data':
        with open(file_path, 'r') as file:
            data = json.load(file)
        return Quantmage_Data.from_json(data)

# # Prepare data for plotting value history with dates
# dates_length = len(data_obj.dates)
# value_history = data_obj.value_history[:dates_length]
# dates = data_obj.dates[:dates_length]

# # Plot value history with dates
# plt.figure(figsize=(12, 6))
# plt.plot(dates, value_history, label='Value History')

# plt.title('Value History Over Time')
# plt.xlabel('Date')
# plt.ylabel('Value')
# plt.xticks(rotation=45)
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()