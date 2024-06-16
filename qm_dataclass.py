from dataclasses import dataclass
from typing import List, Any, Dict
from datetime import datetime
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
    daily_info: List[Day_Info] 
    number_of_days: int 
    days_traded_yearly = 252
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
    
    def rolling_window(self, data, window_size):
        """Helper function to create a rolling window view of the data."""
        shape = data.shape[:-1] + (data.shape[-1] - window_size + 1, window_size)
        strides = data.strides + (data.strides[-1],)
        return np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)
    
    def calculate_correlation(self, other: 'Spell', window_size: int=None) -> Dict[str, List[float]]:
        """Calculate the rolling correlation between this spell's backtest_percent and another spell's backtest_percent
        for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            other (Spell): The other spell to compare against.

        Returns:
            Dict[str, List[float]]: A dictionary with keys 'correlation' and 'yc_to_correlation' containing lists of
                                    the rolling correlation values truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size or len(other.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate correlation for the given window size.")
        
        rolling_windows_self = self.rolling_window(np.array(self.backtest_percent), window_size)
        rolling_windows_other = self.rolling_window(np.array(other.backtest_percent), window_size)
        correlations = []
        yc_to_correlations = []
        
        for window_self, window_other in zip(rolling_windows_self, rolling_windows_other):
            correlation = np.corrcoef(window_self, window_other)[0, 1]
            correlations.append(round(correlation, 2))
        
        rolling_windows_self_yc_to = self.rolling_window(np.array(self.backtest_percent_yc_to), window_size)
        rolling_windows_other_yc_to = self.rolling_window(np.array(other.backtest_percent_yc_to), window_size)
        
        for window_self, window_other in zip(rolling_windows_self_yc_to, rolling_windows_other_yc_to):
            yc_to_correlation = np.corrcoef(window_self, window_other)[0, 1]
            yc_to_correlations.append(round(yc_to_correlation, 2))
        
        return {"correlation": correlations, "yc_to_correlation": yc_to_correlations}
    
    def calculate_cumulative_return(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Cumulative Return % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Cumulative Return % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Cumulative Return for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        cumulative_returns = []
        for window in rolling_windows:
            beginning_value = window[0]
            ending_value = window[-1]
            cumulative_return = ((ending_value / beginning_value) - 1) * 100
            cumulative_returns.append(round(cumulative_return, 2))
        return cumulative_returns
    
    def calculate_annual_return(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Annual Return % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Annual Return % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Annual Return for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        annual_returns = []
        for window in rolling_windows:
            beginning_value = window[0]
            ending_value = window[-1]
            number_of_years = window_size / 252  # Assuming 252 trading days in a year
            annual_return = ((ending_value / beginning_value) ** (1 / number_of_years) - 1) * 100
            annual_returns.append(round(annual_return, 2))
        return annual_returns
    
    def calculate_daily_win_rate(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Daily Win Rate % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Daily Win Rate % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Daily Win Rate for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        daily_win_rates = []
        for window in rolling_windows:
            wins = 0
            for i in range(1, len(window)):
                if window[i] > window[i - 1]:
                    wins += 1
            daily_win_rate = (wins / (len(window) - 1)) * 100
            daily_win_rates.append(round(daily_win_rate, 2))
        return daily_win_rates
    
    def calculate_max_drawdown(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Max Drawdown % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Max Drawdown % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Max Drawdown for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        max_drawdowns = []
        for window in rolling_windows:
            peak = window[0]
            max_drawdown = 0
            for value in window:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            max_drawdowns.append(round(max_drawdown * 100, 2))  # Convert to percentage
        return max_drawdowns
    
    def calculate_cagr(self, window_size: int=None) -> List[float]:
        """Calculate the rolling CAGR % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling CAGR % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate CAGR for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        cagr_list = []
        for window in rolling_windows:
            beginning_value = window[0]
            ending_value = window[-1]
            number_of_years = window_size / self.days_traded_yearly  
            cagr = ((ending_value / beginning_value) ** (1 / number_of_years) - 1) * 100
            cagr_list.append(round(cagr, 2))
        return cagr_list
    
    def calculate_calmar_ratio(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Calmar Ratio based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Calmar Ratio truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Calmar Ratio for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        calmar_ratios = []
        for window in rolling_windows:
            beginning_value = window[0]
            ending_value = window[-1]
            annual_return = ((ending_value / beginning_value) ** (self.days_traded_yearly / window_size) - 1) * 100
            
            peak = window[0]
            max_drawdown = 0
            for value in window:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            max_drawdown *= 100  # Convert to percentage
            if max_drawdown == 0:
                calmar_ratio = float('nan')
            else:
                calmar_ratio = annual_return / max_drawdown
            calmar_ratios.append(round(calmar_ratio, 2))
        return calmar_ratios
    
    def calculate_volatility(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Volatility % based on backtest_percent for a given window size."""
        window_size = window_size if window_size is not None else self.number_of_days
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate volatility for the given window size.")
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        volatilities = []
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            volatility = np.std(daily_returns) * np.sqrt(self.days_traded_yearly) * 100  # Annualize the volatility
            volatilities.append(round(volatility, 2))
        return volatilities
    
    def calculate_sharpe_ratio(self, window_size: int=None, risk_free_rate: float = 0.0) -> List[float]:
        """Calculate the rolling Sharpe Ratio based on backtest_percent for a given window size."""
        window_size = window_size if window_size is not None else self.number_of_days
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Sharpe Ratio for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        sharpe_ratios = []
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            mean_daily_return = np.mean(daily_returns)
            std_dev_daily_return = np.std(daily_returns)
            
            if std_dev_daily_return == 0:
                sharpe_ratios.append(float('nan'))
            else:
                annualized_return = mean_daily_return * self.days_traded_yearly
                annualized_std_dev = std_dev_daily_return * np.sqrt(self.days_traded_yearly)
                sharpe_ratio = (annualized_return - risk_free_rate) / annualized_std_dev
                sharpe_ratios.append(round(sharpe_ratio, 2))
        return sharpe_ratios
    
    def calculate_sortino_ratio(self, window_size: int=None, risk_free_rate: float = 0.0) -> List[float]:
        """Calculate the rolling Sortino Ratio based on backtest_percent for a given window size."""
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Sortino Ratio for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        sortino_ratios = []
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            mean_daily_return = np.mean(daily_returns)
            downside_returns = daily_returns[daily_returns < 0]
            downside_deviation = np.std(downside_returns)
            
            if downside_deviation == 0:
                sortino_ratios.append(float('nan'))
            else:
                annualized_return = mean_daily_return * self.days_traded_yearly
                annualized_downside_deviation = downside_deviation * np.sqrt(self.days_traded_yearly)
                sortino_ratio = (annualized_return - risk_free_rate) / annualized_downside_deviation
                sortino_ratios.append(round(sortino_ratio, 2))
        return sortino_ratios
    
    def calculate_sortino_squared(self, window_size: int=None, risk_free_rate: float = 0.0) -> List[float]:
        """Calculate the rolling Sortino Squared Ratio based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            risk_free_rate (float, optional): The risk-free rate. Defaults to 0.0.

        Returns:
            List[float]: The rolling Sortino Squared Ratio truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        sortino_ratios = self.calculate_sortino_ratio(window_size, risk_free_rate)
        sortino_squared = [round(ratio ** 2, 2) if ratio is not float('nan') else float('nan') for ratio in sortino_ratios]
        return sortino_squared
    
    # NOTE: NOT TESTED
    def calculate_beta(self, market_returns: List[float], window_size: int=None) -> List[float]:
        """Calculate the rolling Beta based on backtest_percent compared to market returns for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            market_returns (List[float]): The list of market returns to compare against.

        Returns:
            List[float]: The rolling Beta values truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size or len(market_returns) < window_size:
            raise ValueError("Not enough data to calculate Beta for the given window size.")
        
        rolling_windows_asset = self.rolling_window(np.array(self.backtest_percent), window_size)
        rolling_windows_market = self.rolling_window(np.array(market_returns), window_size)
        betas = []
        
        for window_asset, window_market in zip(rolling_windows_asset, rolling_windows_market):
            asset_daily_returns = np.diff(window_asset) / window_asset[:-1]
            market_daily_returns = np.diff(window_market) / window_market[:-1]
            
            covariance_matrix = np.cov(asset_daily_returns, market_daily_returns)
            covariance = covariance_matrix[0, 1]
            market_variance = covariance_matrix[1, 1]
            
            if market_variance == 0:
                betas.append(float('nan'))
            else:
                beta = covariance / market_variance
                betas.append(round(beta, 2))
        return betas

    def calculate_mar_ratio(self, window_size: int=None) -> List[float]:
        """Calculate the rolling MAR Ratio based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling MAR Ratio truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate MAR Ratio for the given window size.")
        
        annual_returns = self.calculate_annual_return(window_size)
        max_drawdowns = self.calculate_max_drawdown(window_size)
        mar_ratios = []
        
        for annual_return, max_drawdown in zip(annual_returns, max_drawdowns):
            if max_drawdown == 0:
                mar_ratios.append(float('nan'))
            else:
                mar_ratio = annual_return / max_drawdown
                mar_ratios.append(round(mar_ratio, 2))
        return mar_ratios
    
    def calculate_ulcer_index(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Ulcer Index based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Ulcer Index truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Ulcer Index for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        ulcer_indices = []
        for window in rolling_windows:
            peak = window[0]
            sum_squared_drawdowns = 0
            n = len(window)
            for value in window:
                if value > peak:
                    peak = value
                drawdown = ((peak - value) / peak) * 100  # Calculate percentage drawdown
                sum_squared_drawdowns += drawdown ** 2
            ulcer_index = (sum_squared_drawdowns / n) ** 0.5
            ulcer_indices.append(round(ulcer_index, 2))
        return ulcer_indices

    def calculate_ulcer_performance_index(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Ulcer Performance Index based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Ulcer Performance Index truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Ulcer Performance Index for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        ulcer_indices = self.calculate_ulcer_index(window_size)
        ulcer_performance_indices = []
        
        for i, window in enumerate(rolling_windows):
            beginning_value = window[0]
            ending_value = window[-1]
            number_of_years = window_size / self.days_traded_yearly
            annual_return = ((ending_value / beginning_value) ** (1 / number_of_years) - 1) * 100
            
            ulcer_index = ulcer_indices[i]
            
            if ulcer_index == 0:
                ulcer_performance_indices.append(float('nan'))
            else:
                ulcer_performance_index = annual_return / ulcer_index
                ulcer_performance_indices.append(round(ulcer_performance_index, 2))
        return ulcer_performance_indices

    def calculate_gain_to_pain_ratio(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Gain to Pain Ratio based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Gain to Pain Ratio truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Gain to Pain Ratio for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        gain_to_pain_ratios = []
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            sum_gains = np.sum(daily_returns[daily_returns > 0])
            sum_losses = np.sum(np.abs(daily_returns[daily_returns < 0]))
            
            if sum_losses == 0:
                gain_to_pain_ratios.append(float('nan'))
            else:
                gain_to_pain_ratio = sum_gains / sum_losses
                gain_to_pain_ratios.append(round(gain_to_pain_ratio - 1, 2))
        return gain_to_pain_ratios

    def calculate_standard_deviation(self, window_size: int=None) -> List[float]:
        """Calculate the rolling Standard Deviation % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.

        Returns:
            List[float]: The rolling Standard Deviation % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Standard Deviation for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        standard_deviations = []
        
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            std_dev = np.std(daily_returns) * np.sqrt(252) * 100  # Annualize the standard deviation
            standard_deviations.append(round(std_dev, 2))
        
        return standard_deviations
    
    def calculate_upside_deviation(self, window_size: int=None, target_return: float = 0.0) -> List[float]:
        """Calculate the rolling Upside Deviation % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            target_return (float, optional): The target return for upside deviation calculation. Defaults to 0.0.

        Returns:
            List[float]: The rolling Upside Deviation % truncated to two decimal places.
        """        
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Upside Deviation for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        upside_deviations = []
        
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            upside_returns = daily_returns[daily_returns > target_return]
            upside_deviation = np.std(upside_returns)
            annualized_upside_deviation = upside_deviation * np.sqrt(252) * 100  # Annualize the upside deviation
            upside_deviations.append(round(annualized_upside_deviation, 2))
        
        return upside_deviations
    
    def calculate_downside_deviation(self, window_size: int=None, target_return: float = 0.0) -> List[float]:
        """Calculate the rolling Downside Deviation % based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            target_return (float, optional): The target return for downside deviation calculation. Defaults to 0.0.

        Returns:
            List[float]: The rolling Downside Deviation % truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate downside deviation for the given window size.")
        
        rolling_windows = self.rolling_window(np.array(self.backtest_percent), window_size)
        downside_deviations = []
        for window in rolling_windows:
            daily_returns = np.diff(window) / window[:-1]
            downside_returns = daily_returns[daily_returns < target_return]
            downside_deviation = np.std(downside_returns)
            annualized_downside_deviation = downside_deviation * np.sqrt(self.days_traded_yearly) * 100  # Annualize the downside deviation
            downside_deviations.append(round(annualized_downside_deviation, 2))
        return downside_deviations

    def calculate_carp(self,  other: 'Spell', risk_free_rate: float = 0.0, window_size: int=None) -> List[float]:
        """Calculate the rolling CARP based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            other (Spell): The other spell to compare against.
            risk_free_rate (float, optional): The risk-free rate. Defaults to 0.0.

        Returns:
            List[float]: The rolling CARP values truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size or len(other.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate CARP for the given window size.")

        rolling_windows_self = self.rolling_window(np.array(self.backtest_percent), window_size)
        rolling_windows_other = self.rolling_window(np.array(other.backtest_percent), window_size)
        correlations = self.calculate_correlation(window_size=window_size, other=other)['correlation']
        
        carps = []
        
        for i, (window_self, correlation) in enumerate(zip(rolling_windows_self, correlations)):
            if correlation is float('nan'):
                carps.append(float('nan'))
                continue
            
            # Calculate excess return
            beginning_value = window_self[0]
            ending_value = window_self[-1]
            number_of_years = window_size / self.days_traded_yearly  # Assuming 252 trading days in a year
            annual_return = ((ending_value / beginning_value) ** (1 / number_of_years) - 1) * 100
            excess_return = annual_return - risk_free_rate
            
            # Calculate CARP
            if correlation == 0:
                carps.append(float('nan'))
            else:
                carp = excess_return / correlation
                carps.append(round(carp, 2))
        
        return carps

    def calculate_smart_carp(self, other: 'Spell', risk_free_rate: float = 0.0, window_size: int=None) -> List[float]:
        """Calculate the rolling Smart CARP based on backtest_percent for a given window size.

        Args:
            window_size (int): The size of the rolling window.
            other (Spell): The other spell to compare against.
            risk_free_rate (float, optional): The risk-free rate. Defaults to 0.0.

        Returns:
            List[float]: The rolling Smart CARP values truncated to two decimal places.
        """
        window_size = window_size if window_size is not None else self.number_of_days
        
        if len(self.backtest_percent) < window_size or len(other.backtest_percent) < window_size:
            raise ValueError("Not enough data to calculate Smart CARP for the given window size.")

        rolling_windows_self = self.rolling_window(np.array(self.backtest_percent), window_size)
        rolling_windows_other = self.rolling_window(np.array(other.backtest_percent), window_size)
        correlations = self.calculate_correlation(window_size=window_size, other=other)['correlation']
        volatilities = self.calculate_standard_deviation(window_size=window_size)  # Using standard deviation as a risk measure
        
        smart_carps = []
        
        for i, (window_self, correlation, volatility) in enumerate(zip(rolling_windows_self, correlations, volatilities)):
            if correlation is float('nan') or volatility is float('nan'):
                smart_carps.append(float('nan'))
                continue
            
            # Calculate excess return
            beginning_value = window_self[0]
            ending_value = window_self[-1]
            number_of_years = window_size / 252  # Assuming 252 trading days in a year
            annual_return = ((ending_value / beginning_value) ** (1 / number_of_years) - 1) * 100
            excess_return = annual_return - risk_free_rate
            
            # Calculate Smart CARP
            if correlation == 0:
                smart_carps.append(float('nan'))
            else:
                smart_carp = (excess_return / correlation) / volatility
                smart_carps.append(round(smart_carp, 2))
        
        return smart_carps
    
if __name__ == "__main__":
    mixed = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\81e1430056f8e243f6ff97855738bdca.json")
    print(mixed.name)
    enter = Spell.from_json_file("D:\\Git Repos\\quantmage_api\\ba7158f9bf6d88ea87db0341f6c4a849.json")
    print(enter.name)
    
    print(mixed.calculate_correlation(enter))
    print(mixed.calculate_carp(enter))
    print(mixed.calculate_smart_carp(enter))
    print(f"CAGR: {mixed.calculate_cagr()}")
    print(f"CR: {mixed.calculate_cumulative_return()}")
    print(f"AR: {mixed.calculate_annual_return()}")
    print(f"Daily Win Rate: {mixed.calculate_daily_win_rate()}")
    print(f"MDD: {mixed.calculate_max_drawdown()}")
    print(f"Calmer: {mixed.calculate_calmar_ratio()}")
    print(f"Volatility: {mixed.calculate_volatility()}")
    print(f"Sharpe: {mixed.calculate_sharpe_ratio()}")
    print(f"Sortino: {mixed.calculate_sortino_ratio()}")
    print(f"Sortino Squared: {mixed.calculate_sortino_squared()}")
    print(f"Standard Deviation: {mixed.calculate_standard_deviation()}")
    print(f"Upside Deviation: {mixed.calculate_upside_deviation()}")
    print(f"Downside Deviation: {mixed.calculate_downside_deviation()}")
    print(f"MAR: {mixed.calculate_mar_ratio()}")
    print(f"UPI: {mixed.calculate_ulcer_performance_index()}")
    print(f"GPR: {mixed.calculate_gain_to_pain_ratio()}")
    magic_8_ball()
    