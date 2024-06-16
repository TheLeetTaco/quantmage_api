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
    
    def calculate_cumulative_return(self) -> float:
        """Calculate the Cumulative Return % based on backtest_percent.

        Returns:
            float: The Cumulative Return % truncated to two decimal places.
        """
        if len(self.backtest_percent) == 0:
            raise ValueError("The backtest_percent list is empty.")
        
        beginning_value = self.backtest_percent[0]
        ending_value = self.backtest_percent[-1]
        cumulative_return = (ending_value / beginning_value - 1) * 100
        return round(cumulative_return, 2)
    
    def calculate_annual_return(self) -> float:
        """Calculate the Annual Return % based on backtest_percent.

        Returns:
            float: The Annual Return % truncated to two decimal places.
        """
        if len(self.backtest_percent) == 0:
            raise ValueError("The backtest_percent list is empty.")
        
        beginning_value = self.backtest_percent[0]
        ending_value = self.backtest_percent[-1]
        number_of_years = self.number_of_days / 252  # Assuming 252 trading days in a year
        
        annual_return = (ending_value / beginning_value) ** (1 / number_of_years) - 1
        return round(annual_return * 100, 2)
    
    def calculate_daily_win_rate(self) -> float:
        """Calculate the Daily Win Rate % based on backtest_percent.

        Returns:
            float: The Daily Win Rate % truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate daily win rate.")
        
        wins = 0
        for i in range(1, len(self.backtest_percent)):
            if self.backtest_percent[i] > self.backtest_percent[i - 1]:
                wins += 1
        
        daily_win_rate = (wins / (len(self.backtest_percent) - 1)) * 100
        return round(daily_win_rate, 2)
    
    def calculate_max_drawdown(self) -> float:
        """Calculate the Max Drawdown % based on backtest_percent.

        Returns:
            float: The Max Drawdown % truncated to two decimal places.
        """
        if len(self.backtest_percent) == 0:
            raise ValueError("The backtest_percent list is empty.")
        
        peak = self.backtest_percent[0]
        max_drawdown = 0
        for value in self.backtest_percent:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return round(max_drawdown * 100, 2)
    
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
    
    def calculate_calmar_ratio(self) -> float:
        """Calculate the Calmar Ratio based on backtest_percent.

        Returns:
            float: The Calmar Ratio truncated to two decimal places.
        """
        annual_return = self.calculate_annual_return()
        max_drawdown = self.calculate_max_drawdown()
        
        if max_drawdown == 0:
            raise ValueError("Max Drawdown is zero, cannot calculate Calmar Ratio.")
        
        calmar_ratio = annual_return / max_drawdown
        return round(calmar_ratio, 2)
    
    def calculate_volatility(self) -> float:
        """Calculate the Volatility % based on backtest_percent.

        Returns:
            float: The Volatility % truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate volatility.")
        
        daily_returns = np.diff(self.backtest_percent) / self.backtest_percent[:-1]
        volatility = np.std(daily_returns) * np.sqrt(252) * 100  # Annualize the volatility
        return round(volatility, 2)
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate the Sharpe Ratio based on backtest_percent.

        Args:
            risk_free_rate (float, optional): The risk-free rate. Defaults to 0.0.

        Returns:
            float: The Sharpe Ratio truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate Sharpe Ratio.")
        
        # Calculate daily returns
        daily_returns = np.diff(self.backtest_percent) / self.backtest_percent[:-1]
        
        # Calculate the mean and standard deviation of daily returns
        mean_daily_return = np.mean(daily_returns)
        std_dev_daily_return = np.std(daily_returns)
        
        if std_dev_daily_return == 0:
            raise ValueError("Standard deviation of daily returns is zero, cannot calculate Sharpe Ratio.")
        
        # Annualize the mean daily return and standard deviation
        annualized_return = mean_daily_return * 252
        annualized_std_dev = std_dev_daily_return * np.sqrt(252)
        
        # Calculate the Sharpe Ratio
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_std_dev
        return round(sharpe_ratio, 2)
    
    # NOTE: Possibly incorrect calculation
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate the Sortino Ratio based on backtest_percent.

        Args:
            risk_free_rate (float, optional): The risk-free rate. Defaults to 0.0.

        Returns:
            float: The Sortino Ratio truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate Sortino Ratio.")
        
        # Calculate daily returns
        daily_returns = np.diff(self.backtest_percent) / self.backtest_percent[:-1]
        
        # Calculate the mean daily return
        mean_daily_return = np.mean(daily_returns)
        
        # Calculate the downside deviation (only considering negative returns)
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = np.std(downside_returns)
        
        if downside_deviation == 0:
            raise ValueError("Downside deviation of returns is zero, cannot calculate Sortino Ratio.")
        
        # Annualize the mean daily return and downside deviation
        annualized_return = mean_daily_return * 252
        annualized_downside_deviation = downside_deviation * np.sqrt(252)
        
        # Calculate the Sortino Ratio
        sortino_ratio = (annualized_return - risk_free_rate) / annualized_downside_deviation
        return round(sortino_ratio, 2)
    
    # NOTE: NOT TESTED
    def calculate_beta(self, market_returns: List[float]) -> float:
        """Calculate the Beta based on backtest_percent compared to market returns.

        Args:
            market_returns (List[float]): The list of market returns to compare against.

        Returns:
            float: The Beta value truncated to two decimal places.
        """
        if len(self.backtest_percent) != len(market_returns):
            raise ValueError("The length of backtest_percent and market_returns must be the same.")
        
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate Beta.")
        
        # Calculate daily returns for the asset
        asset_daily_returns = np.diff(self.backtest_percent) / self.backtest_percent[:-1]
        
        # Calculate daily returns for the market
        market_daily_returns = np.diff(market_returns) / market_returns[:-1]
        
        # Calculate covariance matrix
        covariance_matrix = np.cov(asset_daily_returns, market_daily_returns)
        
        # Extract covariance between asset and market
        covariance = covariance_matrix[0, 1]
        
        # Extract variance of market returns
        market_variance = covariance_matrix[1, 1]
        
        if market_variance == 0:
            raise ValueError("Variance of market returns is zero, cannot calculate Beta.")
        
        # Calculate Beta
        beta = covariance / market_variance
        return round(beta, 2)

    def calculate_mar_ratio(self) -> float:
        """Calculate the MAR Ratio.

        Returns:
            float: The MAR Ratio truncated to two decimal places.
        """
        annual_return = self.calculate_annual_return()
        max_drawdown = self.calculate_max_drawdown()
        
        if max_drawdown == 0:
            raise ValueError("Max Drawdown is zero, cannot calculate MAR Ratio.")
        
        mar_ratio = annual_return / max_drawdown
        return round(mar_ratio, 2)
    
    def calculate_ulcer_index(self) -> float:
        """Calculate the Ulcer Index based on backtest_percent.

        Returns:
            float: The Ulcer Index truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate Ulcer Index.")
        
        peak = self.backtest_percent[0]
        sum_squared_drawdowns = 0
        n = len(self.backtest_percent)
        
        for value in self.backtest_percent:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100  # Calculate percentage drawdown
            sum_squared_drawdowns += drawdown ** 2
        
        ulcer_index = (sum_squared_drawdowns / n) ** 0.5
        return round(ulcer_index, 2)

    def calculate_ulcer_performance_index(self) -> float:
        """Calculate the Ulcer Performance Index.

        Returns:
            float: The Ulcer Performance Index truncated to two decimal places.
        """
        annual_return = self.calculate_annual_return()
        ulcer_index = self.calculate_ulcer_index()
        
        if ulcer_index == 0:
            raise ValueError("Ulcer Index is zero, cannot calculate Ulcer Performance Index.")
        
        ulcer_performance_index = annual_return / ulcer_index
        return round(ulcer_performance_index, 2)

    def calculate_gain_to_pain_ratio(self) -> float:
        """Calculate the Gain to Pain Ratio based on backtest_percent.

        Returns:
            float: The Gain to Pain Ratio truncated to two decimal places.
        """
        if len(self.backtest_percent) < 2:
            raise ValueError("Not enough data to calculate Gain to Pain Ratio.")
        
        daily_returns = np.diff(self.backtest_percent) / self.backtest_percent[:-1]
        sum_gains = np.sum(daily_returns[daily_returns > 0])
        sum_losses = np.sum(np.abs(daily_returns[daily_returns < 0]))
        
        if sum_losses == 0:
            raise ValueError("Sum of losses is zero, cannot calculate Gain to Pain Ratio.")
        
        gain_to_pain_ratio = sum_gains / sum_losses
        return round(gain_to_pain_ratio - 1, 2)

    
if __name__ == "__main__":
    mixed = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\81e1430056f8e243f6ff97855738bdca.json")
    print(mixed.name)
    enter = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\ba7158f9bf6d88ea87db0341f6c4a849.json")
    print(enter.name)
    
    # print(enter.calc_corelation(enter))
    print(f"CAGR: {enter.calculate_cagr()}")
    print(f"CR: {enter.calculate_cumulative_return()}")
    print(f"AR: {enter.calculate_annual_return()}")
    print(f"Daily Win Rate: {enter.calculate_daily_win_rate()}")
    print(f"MDD: {enter.calculate_max_drawdown()}")
    print(f"Calmer: {enter.calculate_calmar_ratio()}")
    print(f"Volatility: {enter.calculate_volatility()}")
    print(f"Sharpe: {enter.calculate_sharpe_ratio()}")
    print(f"Sortino: {enter.calculate_sortino_ratio()}")
    print(f"MAR: {enter.calculate_mar_ratio()}")
    print(f"UPI: {enter.calculate_ulcer_performance_index()}")
    print(f"GPR: {enter.calculate_gain_to_pain_ratio()}")
    