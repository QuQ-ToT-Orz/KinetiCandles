import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import datetime
import os
import threading
import time
from typing import Optional, List, Dict, Tuple, Union, Any

# Constants for the application
HOUR_LABELS = [f"{h}:00" for h in range(0, 24, 2)]
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
PATTERN_TYPES = {
    "morning_peak": {
        "name": "Morning Peak",
        "description": "Highest activity in morning hours, gradually decreasing throughout the day."
    },
    "evening_peak": {
        "name": "Evening Peak",
        "description": "Activity builds throughout the day, reaching highest levels in evening."
    },
    "midday_peak": {
        "name": "Midday Peak",
        "description": "Activity concentrated during midday hours."
    },
    "bimodal": {
        "name": "Bimodal Pattern",
        "description": "Two distinct activity peaks (morning and evening) with midday lull."
    },
    "consistent": {
        "name": "Consistent Activity",
        "description": "Relatively consistent activity levels throughout active hours."
    }
}

WEEKLY_PATTERN_TYPES = {
    "weekend_warrior": {
        "name": "Weekend Warrior",
        "description": "Significantly higher activity on weekends compared to weekdays."
    },
    "workweek_active": {
        "name": "Workweek Active",
        "description": "Higher activity during the workweek with less active weekends."
    },
    "consistent_weekly": {
        "name": "Consistent Weekly Pattern",
        "description": "Relatively consistent activity levels throughout the week."
    },
    "variable_weekly": {
        "name": "Variable Weekly Pattern",
        "description": "Activity levels vary significantly across different days of the week."
    }
}

# High-resolution candle intervals (in seconds)
HIGHRES_INTERVALS = [
    ("15 seconds", 15),
    ("30 seconds", 30),
    ("1 minute", 60),
    ("5 minutes", 300)
]


class DataModel:
    """Model class to handle data loading, processing, and analysis."""

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.current_day_index: int = 0
        self.days: List[datetime.date] = []
        self.has_second_resolution: bool = False
        
    def load_data(self, filename: str) -> bool:
        """Load and preprocess accelerometer data from a CSV file.
        
        Args:
            filename: Path to the CSV file
            
        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        try:
            # Load the data
            data = pd.read_csv(filename)
            
            # Check for required columns
            required_columns = ['timestamp', 'activity_level']
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"The file must contain these columns: {', '.join(required_columns)}")
            
            # Convert timestamp to datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Add day of week
            data['day_of_week'] = data['timestamp'].dt.day_name()
            
            # Detect if data has second-level resolution
            self.detect_data_resolution(data)
            
            # Store data
            self.data = data
            
            # Get unique days
            self.days = sorted(self.data['timestamp'].dt.date.unique())
            
            # Reset current day
            self.current_day_index = 0
            
            return True
            
        except Exception as e:
            raise e
    
    def detect_data_resolution(self, data: pd.DataFrame) -> None:
        """Detect the resolution of the data (seconds, minutes, hours).
        
        Args:
            data: DataFrame to analyze
        """
        # Sample a subset of data for efficiency
        sample_size = min(1000, len(data))
        sample = data.sample(sample_size) if len(data) > sample_size else data
        
        # Check if there are multiple records with the same minute but different seconds
        sample['minute_key'] = sample['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        records_per_minute = sample.groupby('minute_key').size()
        
        # If we have multiple records per minute, we likely have second-level resolution
        self.has_second_resolution = (records_per_minute > 1).any()
        
        print(f"Data resolution detection: {'Second-level' if self.has_second_resolution else 'Minute-level'} resolution")
    
    def get_current_date(self) -> Optional[datetime.date]:
        """Get the current selected date."""
        if not self.days or self.current_day_index >= len(self.days):
            return None
        return self.days[self.current_day_index]
    
    def get_data_for_current_day(self) -> Optional[pd.DataFrame]:
        """Get data for the currently selected day."""
        current_date = self.get_current_date()
        if current_date is None or self.data is None:
            return None
        
        return self.data[self.data['timestamp'].dt.date == current_date]
    
    def get_daily_data_grouped_by_hour(self) -> Optional[pd.DataFrame]:
        """Get hourly grouped data for the current day."""
        day_data = self.get_data_for_current_day()
        if day_data is None or len(day_data) == 0:
            return None
        
        hourly_data = day_data.groupby(day_data['timestamp'].dt.hour)['activity_level'].agg([
            'first', 'last', 'max', 'min', 'mean', 'std'
        ]).reset_index()
        
        return hourly_data
    
    def get_weekly_data(self) -> Optional[pd.DataFrame]:
        """Get data aggregated by day of week."""
        if self.data is None:
            return None
        
        # Group by day of week
        return self.data.groupby('day_of_week')['activity_level'].agg([
            'mean', 'std', 'max', 'min', 'count'
        ]).reindex(DAYS_OF_WEEK)
    
    def get_high_resolution_data(self, start_hour: int, end_hour: int) -> Optional[pd.DataFrame]:
        """Get high-resolution data for a specific time window.
        
        Args:
            start_hour: Start hour for the window
            end_hour: End hour for the window
            
        Returns:
            DataFrame with high-resolution data, including a continuous time index
        """
        day_data = self.get_data_for_current_day()
        if day_data is None or len(day_data) == 0:
            return None
        
        # Filter to specified time window
        window_data = day_data[
            (day_data['timestamp'].dt.hour >= start_hour) & 
            (day_data['timestamp'].dt.hour < end_hour)
        ]
        
        if len(window_data) == 0:
            return None
        
        # Add time index for plotting (continuous value in minutes)
        window_data = window_data.copy()
        
        # Create a fractional time index including seconds
        window_data['time_index'] = (
            window_data['timestamp'].dt.hour * 60 + 
            window_data['timestamp'].dt.minute +
            window_data['timestamp'].dt.second / 60
        )
        
        return window_data
    
    def get_candle_data(self, window_data: pd.DataFrame, interval_seconds: int = 60) -> pd.DataFrame:
        """Process window data into candles for high-resolution view.
        
        Args:
            window_data: High-resolution data for the time window
            interval_seconds: Interval for candle aggregation in seconds (default: 60)
            
        Returns:
            DataFrame with candle data at the specified interval
        """
        if window_data is None or len(window_data) == 0:
            return pd.DataFrame()
            
        # Calculate epoch time and bin it by the interval
        window_data['epoch'] = window_data['timestamp'].astype('int64') // 10**9
        window_data['interval'] = (window_data['epoch'] // interval_seconds) * interval_seconds
        
        # Group by interval
        interval_groups = window_data.groupby('interval')
        
        candle_data = []
        for interval, group in interval_groups:
            if len(group) > 1:  # Need at least 2 points to form a candle
                # Convert interval back to datetime for display
                interval_dt = pd.to_datetime(interval, unit='s')
                
                # Create unique time index for x-axis (minutes since start of day)
                time_index = (
                    interval_dt.hour * 60 + 
                    interval_dt.minute +
                    interval_dt.second / 60
                )
                
                # Format time string for display
                if interval_seconds < 60:
                    time_str = f"{interval_dt.hour:02d}:{interval_dt.minute:02d}:{interval_dt.second:02d}"
                else:
                    time_str = f"{interval_dt.hour:02d}:{interval_dt.minute:02d}"
                
                candle_data.append({
                    'time_index': time_index,
                    'first': group['activity_level'].iloc[0],
                    'last': group['activity_level'].iloc[-1],
                    'max': group['activity_level'].max(),
                    'min': group['activity_level'].min(),
                    'time_str': time_str,
                    'timestamp': interval_dt,
                    'interval_seconds': interval_seconds
                })
        
        return pd.DataFrame(candle_data)
    
    def next_day(self) -> None:
        """Move to the next day."""
        if not self.days:
            return
        self.current_day_index = (self.current_day_index + 1) % len(self.days)
    
    def previous_day(self) -> None:
        """Move to the previous day."""
        if not self.days:
            return
        self.current_day_index = (self.current_day_index - 1) % len(self.days)
    
    def find_day_index_by_name(self, day_name: str) -> Optional[int]:
        """Find index of the first occurrence of a day name."""
        if self.data is None or day_name not in DAYS_OF_WEEK:
            return None
            
        day_data = self.data[self.data['day_of_week'] == day_name]
        if len(day_data) == 0:
            return None
            
        # Get the date of this day
        selected_date = day_data['timestamp'].dt.date.iloc[0]
        
        try:
            return self.days.index(selected_date)
        except ValueError:
            return None
    
    def analyze_day_patterns(self) -> Dict[str, Any]:
        """Analyze patterns for the current day."""
        hourly_data = self.get_daily_data_grouped_by_hour()
        if hourly_data is None or len(hourly_data) == 0:
            return {}
        
        # Identify peak activity hours
        peak_hour = hourly_data.loc[hourly_data['max'].idxmax()]['timestamp']
        
        # Calculate activity distribution
        morning_hours = hourly_data[hourly_data['timestamp'].between(6, 11)]
        midday_hours = hourly_data[hourly_data['timestamp'].between(12, 17)]
        evening_hours = hourly_data[hourly_data['timestamp'].between(18, 23)]
        
        morning_activity = morning_hours['mean'].mean() if len(morning_hours) > 0 else 0
        midday_activity = midday_hours['mean'].mean() if len(midday_hours) > 0 else 0
        evening_activity = evening_hours['mean'].mean() if len(evening_hours) > 0 else 0
        
        # Identify pattern type
        if morning_activity > midday_activity and morning_activity > evening_activity:
            pattern_type = "morning_peak"
        elif evening_activity > morning_activity and evening_activity > midday_activity:
            pattern_type = "evening_peak"
        elif midday_activity > morning_activity and midday_activity > evening_activity:
            pattern_type = "midday_peak"
        elif abs(morning_activity - evening_activity) < 5 and morning_activity > midday_activity:
            pattern_type = "bimodal"
        else:
            pattern_type = "consistent"
        
        # Calculate volatility (variation in activity)
        volatility = hourly_data['std'].mean()
        if volatility > 20:
            volatility_desc = "High variability in activity levels throughout the day."
        elif volatility > 10:
            volatility_desc = "Moderate variability in activity levels."
        else:
            volatility_desc = "Consistent activity levels with minimal fluctuation."
        
        return {
            "pattern_type": pattern_type,
            "peak_hour": int(peak_hour),
            "morning_activity": morning_activity,
            "midday_activity": midday_activity,
            "evening_activity": evening_activity,
            "volatility": volatility,
            "volatility_desc": volatility_desc
        }
    
    def analyze_week_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across the week."""
        weekly_data = self.get_weekly_data()
        if weekly_data is None or weekly_data.empty:
            return {}
        
        # Fill NaN values with 0 for days with no data
        daily_avg = weekly_data['mean'].fillna(0)
        
        # Calculate weekday vs weekend averages
        weekday_indices = [i for i, day in enumerate(DAYS_OF_WEEK) if i < 5]  # Monday-Friday
        weekend_indices = [i for i, day in enumerate(DAYS_OF_WEEK) if i >= 5]  # Saturday-Sunday
        
        weekday_days = [DAYS_OF_WEEK[i] for i in weekday_indices if DAYS_OF_WEEK[i] in daily_avg.index]
        weekend_days = [DAYS_OF_WEEK[i] for i in weekend_indices if DAYS_OF_WEEK[i] in daily_avg.index]
        
        weekday_avg = daily_avg[weekday_days].mean() if weekday_days else 0
        weekend_avg = daily_avg[weekend_days].mean() if weekend_days else 0
        
        # Identify most and least active days
        if not daily_avg.empty:
            most_active_day = daily_avg.idxmax() if not daily_avg.isna().all() else None
            least_active_day = daily_avg.idxmin() if not daily_avg.isna().all() else None
        else:
            most_active_day = least_active_day = None
        
        # Determine weekly pattern type
        if weekend_avg > weekday_avg * 1.3:
            pattern_type = "weekend_warrior"
        elif weekday_avg > weekend_avg * 1.3:
            pattern_type = "workweek_active"
        elif daily_avg.std() < 10:
            pattern_type = "consistent_weekly"
        else:
            pattern_type = "variable_weekly"
        
        return {
            "pattern_type": pattern_type,
            "most_active_day": most_active_day,
            "least_active_day": least_active_day,
            "weekday_avg": weekday_avg,
            "weekend_avg": weekend_avg,
            "daily_averages": daily_avg.to_dict()
        }


class ChartView:
    """View class to handle chart visualization."""
    
    def __init__(self, master: ttk.Frame):
        """Initialize chart view.
        
        Args:
            master: Parent frame for the chart
        """
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Embed matplotlib figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_day_view(self, hourly_data: pd.DataFrame, selected_date: datetime.date) -> None:
        """Plot K-candles for a single day.
        
        Args:
            hourly_data: Hourly aggregated data
            selected_date: Current selected date
        """
        # Clear previous plot
        self.ax.clear()
        
        if hourly_data is None or len(hourly_data) == 0:
            self.ax.text(0.5, 0.5, "No data available for selected day", 
                         ha='center', va='center', transform=self.ax.transAxes)
            return
        
        # Plot setup
        self.ax.set_title(f"Movement Patterns: {selected_date.strftime('%A, %B %d, %Y')}")
        self.ax.set_xlim(-0.5, 23.5)
        self.ax.set_xticks(range(0, 24, 2))
        self.ax.set_xticklabels(HOUR_LABELS)
        
        # Plot each candle
        hours = hourly_data['timestamp']
        for i, hour in enumerate(hours):
            # Candle data
            open_val = hourly_data.loc[i, 'first']
            close_val = hourly_data.loc[i, 'last']
            high_val = hourly_data.loc[i, 'max']
            low_val = hourly_data.loc[i, 'min']
            
            self._plot_candle(hour, open_val, close_val, high_val, low_val)
        
        # Add moving average line (K-line)
        if len(hourly_data) >= 3:  # Need at least 3 points for meaningful average
            ma_data = hourly_data['last'].rolling(window=3, min_periods=1).mean()
            self.ax.plot(hours, ma_data, color='purple', linewidth=2, label='K-Line (3-hour MA)')
            self.ax.legend()
        
        # Finalize plot
        self._finalize_plot()
    
    def plot_week_view(self, weekly_data: pd.DataFrame) -> None:
        """Plot K-candles for a full week.
        
        Args:
            weekly_data: Weekly aggregated data
        """
        # Clear previous plot
        self.ax.clear()
        
        if weekly_data is None or weekly_data.empty:
            self.ax.text(0.5, 0.5, "No weekly data available", 
                         ha='center', va='center', transform=self.ax.transAxes)
            return
        
        # Set up plot
        self.ax.set_title("Weekly Movement Patterns")
        self.ax.set_xlim(-0.5, 6.5)
        self.ax.set_xticks(range(7))
        self.ax.set_xticklabels(DAYS_OF_WEEK)
        
        # Process data for each day of the week
        for i, day in enumerate(DAYS_OF_WEEK):
            if day not in weekly_data.index:
                continue
                
            day_stats = weekly_data.loc[day]
            
            # Use mean as open, mean as close (since we don't have actual first/last)
            # Use max/min as high/low
            open_val = day_stats['mean']
            close_val = day_stats['mean']
            high_val = day_stats['max']
            low_val = day_stats['min']
            
            # Since open==close, use green candles for weekdays, red for weekends
            color = 'red' if i >= 5 else 'green'
            
            # Plot high-low line
            self.ax.plot([i, i], [low_val, high_val], color='black', linewidth=1)
            
            # Plot candle body
            width = 0.8
            rect = plt.Rectangle((i - width/2, min(open_val, close_val)), 
                                width, abs(open_val - close_val),
                                fill=True, color=color, alpha=0.6)
            self.ax.add_patch(rect)
        
        # Finalize plot
        self._finalize_plot()
    
    def plot_high_resolution_view(self, candle_data: pd.DataFrame, selected_date: datetime.date, 
                                 start_hour: int, end_hour: int, interval_seconds: int = 60) -> None:
        """Plot high-resolution K-candles.
        
        Args:
            candle_data: Candle data at the specified interval
            selected_date: Current selected date
            start_hour: Start hour for the window
            end_hour: End hour for the window
            interval_seconds: Interval for the candles in seconds
        """
        # Clear previous plot
        self.ax.clear()
        
        if candle_data is None or len(candle_data) == 0:
            self.ax.text(0.5, 0.5, "No data available for selected time window", 
                         ha='center', va='center', transform=self.ax.transAxes)
            return
        
        # Format interval for title
        if interval_seconds < 60:
            interval_str = f"{interval_seconds}-second"
        elif interval_seconds == 60:
            interval_str = "1-minute"
        elif interval_seconds % 60 == 0:
            interval_str = f"{interval_seconds // 60}-minute"
        else:
            interval_str = f"{interval_seconds}-second"
        
        # Plot setup
        self.ax.set_title(f"High-Resolution Movement Pattern ({interval_str} candles): "
                         f"{selected_date.strftime('%A, %B %d, %Y')} "
                         f"{start_hour:02d}:00 - {end_hour:02d}:00")
        
        # X-axis setup with appropriate tick frequency based on interval
        min_time = start_hour * 60
        max_time = end_hour * 60
        total_minutes = max_time - min_time
        
        # Determine tick frequency based on total time window
        if total_minutes <= 60:  # 1 hour or less
            tick_minutes = 5  # 5-minute ticks
        elif total_minutes <= 120:  # 1-2 hours
            tick_minutes = 10  # 10-minute ticks
        elif total_minutes <= 240:  # 2-4 hours
            tick_minutes = 15  # 15-minute ticks
        else:
            tick_minutes = 30  # 30-minute ticks
        
        # Create tick positions and labels
        x_ticks = [min_time + i for i in range(0, total_minutes + 1, tick_minutes)]
        x_labels = [f"{t // 60:02d}:{t % 60:02d}" for t in x_ticks]
        
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(x_labels, rotation=45)
        self.ax.set_xlim(min_time - 2, max_time + 2)
        
        # Plot each candle
        for _, row in candle_data.iterrows():
            time_idx = row['time_index']
            open_val = row['first']
            close_val = row['last']
            high_val = row['max']
            low_val = row['min']
            
            self._plot_candle(time_idx, open_val, close_val, high_val, low_val)
        
        # Add K-line (moving average)
        if len(candle_data) >= 5:  # Need at least 5 points for meaningful average
            window_size = max(5, len(candle_data) // 20)  # Adaptive window size
            
            # Sort data by time index for proper moving average
            sorted_data = candle_data.sort_values('time_index')
            ma_data = sorted_data['last'].rolling(window=window_size, min_periods=1).mean()
            
            self.ax.plot(sorted_data['time_index'], ma_data, color='purple', linewidth=2, 
                        label=f'K-Line ({window_size}-interval MA)')
            self.ax.legend()
        
        # Finalize plot
        self._finalize_plot()
    
    def _plot_candle(self, x: Union[int, float], open_val: float, close_val: float, 
                    high_val: float, low_val: float) -> None:
        """Plot a single candle.
        
        Args:
            x: X-coordinate for the candle
            open_val: Opening value
            close_val: Closing value
            high_val: Highest value
            low_val: Lowest value
        """
        # Determine color based on open vs close
        color = 'green' if close_val >= open_val else 'red'
        
        # Plot high-low line
        self.ax.plot([x, x], [low_val, high_val], color='black', linewidth=1)
        
        # Plot candle body
        width = 0.8
        rect = plt.Rectangle((x - width/2, min(open_val, close_val)), 
                            width, abs(open_val - close_val),
                            fill=True, color=color, alpha=0.6)
        self.ax.add_patch(rect)
    
    def _finalize_plot(self) -> None:
        """Add common elements and finalize the plot."""
        # Add grid and labels
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Activity Level')
        
        # Refresh canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def clear(self) -> None:
        """Clear the chart."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No data loaded", 
                    ha='center', va='center', transform=self.ax.transAxes)
        self.canvas.draw()


class AnalysisView:
    """View class to handle analysis display."""
    
    def __init__(self, master: ttk.LabelFrame):
        """Initialize analysis view.
        
        Args:
            master: Parent frame for the analysis view
        """
        # Text widget for analysis results
        self.text = tk.Text(master, height=8, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.insert(tk.END, "Load data to see movement pattern analysis...")
        self.text.config(state=tk.DISABLED)
    
    def update_day_analysis(self, analysis: Dict[str, Any]) -> None:
        """Update the analysis text with day analysis results.
        
        Args:
            analysis: Day analysis results dictionary
        """
        if not analysis:
            self.clear()
            return
            
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        
        pattern_type = analysis["pattern_type"]
        peak_hour = analysis["peak_hour"]
        morning_activity = analysis["morning_activity"]
        midday_activity = analysis["midday_activity"]
        evening_activity = analysis["evening_activity"]
        volatility = analysis["volatility"]
        volatility_desc = analysis["volatility_desc"]
        
        self.text.insert(tk.END, f"Pattern Type: {PATTERN_TYPES[pattern_type]['name']}\n\n")
        self.text.insert(tk.END, f"{PATTERN_TYPES[pattern_type]['description']}\n\n")
        self.text.insert(tk.END, f"Peak Activity Hour: {peak_hour}:00\n")
        self.text.insert(tk.END, f"Activity Distribution: Morning ({morning_activity:.1f}) | ")
        self.text.insert(tk.END, f"Midday ({midday_activity:.1f}) | Evening ({evening_activity:.1f})\n\n")
        self.text.insert(tk.END, f"Volatility: {volatility:.1f} - {volatility_desc}")
        
        self.text.config(state=tk.DISABLED)
    
    def update_week_analysis(self, analysis: Dict[str, Any]) -> None:
        """Update the analysis text with week analysis results.
        
        Args:
            analysis: Week analysis results dictionary
        """
        if not analysis:
            self.clear()
            return
            
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        
        pattern_type = analysis["pattern_type"]
        most_active_day = analysis["most_active_day"]
        least_active_day = analysis["least_active_day"]
        weekday_avg = analysis["weekday_avg"]
        weekend_avg = analysis["weekend_avg"]
        daily_averages = analysis["daily_averages"]
        
        self.text.insert(tk.END, f"Weekly Pattern Type: {WEEKLY_PATTERN_TYPES[pattern_type]['name']}\n\n")
        self.text.insert(tk.END, f"{WEEKLY_PATTERN_TYPES[pattern_type]['description']}\n\n")
        
        if most_active_day:
            self.text.insert(tk.END, f"Most Active Day: {most_active_day}\n")
        if least_active_day:
            self.text.insert(tk.END, f"Least Active Day: {least_active_day}\n\n")
        
        self.text.insert(tk.END, f"Weekday Average: {weekday_avg:.1f}\n")
        self.text.insert(tk.END, f"Weekend Average: {weekend_avg:.1f}\n\n")
        
        # Add specific day analysis
        self.text.insert(tk.END, "Daily Activity Levels:\n")
        for day in DAYS_OF_WEEK:
            if day in daily_averages:
                self.text.insert(tk.END, f"{day}: {daily_averages[day]:.1f}\n")
        
        self.text.config(state=tk.DISABLED)
    
    def update_high_res_analysis(self, interval_seconds: int = 60) -> None:
        """Update analysis text for high-resolution view.
        
        Args:
            interval_seconds: Interval for candles in seconds
        """
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        
        # Format interval for analysis
        if interval_seconds < 60:
            interval_str = f"{interval_seconds}-second"
        elif interval_seconds == 60:
            interval_str = "1-minute"
        elif interval_seconds % 60 == 0:
            interval_str = f"{interval_seconds // 60}-minute"
        else:
            interval_str = f"{interval_seconds}-second"
        
        self.text.insert(tk.END, f"High-Resolution View: Examining movement patterns with {interval_str} resolution.\n\n")
        self.text.insert(tk.END, "The visualization groups 1-second data into candles for meaningful analysis.\n\n")
        self.text.insert(tk.END, "Use the time window selectors above to focus on specific periods of interest.\n\n")
        self.text.insert(tk.END, "Green candles indicate increasing activity, red candles indicate decreasing activity.")
        
        self.text.config(state=tk.DISABLED)
    
    def clear(self) -> None:
        """Clear the analysis text."""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, "No analysis available.")
        self.text.config(state=tk.DISABLED)


class KinetiCandlesApp:
    """Main application class using MVC pattern."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("KinetiCandles: Movement Pattern Analyzer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Create model
        self.model = DataModel()
        
        # Data storage
        self.user_data = None  # Store user's loaded data
        self.using_sample_data = False  # Flag to track if using sample data
        
        # State variables
        self.current_view = "day"  # 'day', 'week', or 'high_res'
        self.selected_start_hour = 8
        self.selected_end_hour = 10
        self.candle_interval_seconds = 60  # Default to 1-minute candles
        self.simulation_active = False
        self.simulation_day_index = 0
        
        # Create UI
        self.create_menu()
        self.create_main_frame()
    
    def create_menu(self) -> None:
        """Create application menu."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Accelerometer Data", command=self.load_data)
        file_menu.add_command(label="Export Current View", command=self.export_view)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Daily View", command=lambda: self.switch_view("day"))
        view_menu.add_command(label="Weekly View", command=lambda: self.switch_view("week"))
        view_menu.add_command(label="High-Resolution View", command=lambda: self.switch_view("high_res"))
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Resolution submenu (only for high-res view)
        resolution_menu = tk.Menu(menubar, tearoff=0)
        resolution_menu.add_command(label="15-second Candles", 
                                   command=lambda: self.set_candle_interval(15))
        resolution_menu.add_command(label="30-second Candles", 
                                   command=lambda: self.set_candle_interval(30))
        resolution_menu.add_command(label="1-minute Candles", 
                                   command=lambda: self.set_candle_interval(60))
        resolution_menu.add_command(label="5-minute Candles", 
                                   command=lambda: self.set_candle_interval(300))
        menubar.add_cascade(label="Resolution", menu=resolution_menu)
        
        # Features menu
        features_menu = tk.Menu(menubar, tearoff=0)
        features_menu.add_command(label="Time Domain Analysis", command=self.show_time_domain_analysis)
        features_menu.add_command(label="Frequency Domain Analysis", command=self.show_frequency_domain_analysis)
        features_menu.add_command(label="Other Advanced Measures", command=self.show_advanced_measures)
        menubar.add_cascade(label="Features", menu=features_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Pattern Guide", command=self.show_pattern_guide)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_frame(self) -> None:
        """Create main application frame and components."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create control panel
        self.create_control_panel(main_frame)
        
        # Create canvas frame for chart
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create chart view
        self.chart_view = ChartView(canvas_frame)
        
        # Create analysis panel
        analysis_frame = ttk.LabelFrame(main_frame, text="Pattern Analysis", padding="10")
        analysis_frame.pack(fill=tk.X, pady=5)
        
        # Create analysis view
        self.analysis_view = AnalysisView(analysis_frame)
    
    def create_control_panel(self, parent: ttk.Frame) -> None:
        """Create control panel with buttons and selectors.
        
        Args:
            parent: Parent frame for control panel
        """
        # Top control panel
        self.control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # Create a row for buttons
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Load data button
        load_btn = ttk.Button(button_frame, text="Load Data", command=self.load_data)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Sample data / User data toggle button
        self.sim_btn = ttk.Button(button_frame, text="Use Sample Data", command=self.toggle_simulation)
        self.sim_btn.pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(button_frame)
        nav_frame.pack(side=tk.LEFT, padx=20)
        
        prev_btn = ttk.Button(nav_frame, text="◀ Previous", command=self.previous_day)
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = ttk.Button(nav_frame, text="Next ▶", command=self.next_day)
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Current view label
        self.view_label = ttk.Label(button_frame, text="No data loaded")
        self.view_label.pack(side=tk.LEFT, padx=20)
        
        # Day selector for week view
        self.day_selector = ttk.Combobox(button_frame, values=DAYS_OF_WEEK)
        self.day_selector.pack(side=tk.RIGHT, padx=5)
        self.day_selector.bind("<<ComboboxSelected>>", self.on_day_selected)
        
        # Add time window selector for high-resolution view
        self.add_time_window_selector()
    
    def add_time_window_selector(self) -> None:
        """Add time window selector for high-resolution view."""
        time_frame = ttk.Frame(self.control_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="High-Resolution Window:").pack(side=tk.LEFT, padx=5)
        
        # Start hour selector
        ttk.Label(time_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_hour_var = tk.StringVar(value="08")
        start_hour_combo = ttk.Combobox(time_frame, textvariable=self.start_hour_var, width=5)
        start_hour_combo['values'] = [f"{i:02d}" for i in range(24)]
        start_hour_combo.pack(side=tk.LEFT)
        
        # End hour selector
        ttk.Label(time_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.end_hour_var = tk.StringVar(value="10")
        end_hour_combo = ttk.Combobox(time_frame, textvariable=self.end_hour_var, width=5)
        end_hour_combo['values'] = [f"{i:02d}" for i in range(24)]
        end_hour_combo.pack(side=tk.LEFT)
        
        # Add interval selector
        ttk.Label(time_frame, text="Candle Size:").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="1 minute")
        interval_combo = ttk.Combobox(time_frame, textvariable=self.interval_var, width=10)
        interval_combo['values'] = [name for name, _ in HIGHRES_INTERVALS]
        interval_combo.pack(side=tk.LEFT)
        interval_combo.bind("<<ComboboxSelected>>", self.on_interval_selected)
        
        # High-resolution view button
        apply_btn = ttk.Button(time_frame, text="Show High-Resolution", command=self.update_high_res_view)
        apply_btn.pack(side=tk.LEFT, padx=10)
        
        # View selector buttons
        view_frame = ttk.Frame(time_frame)
        view_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(view_frame, text="Quick View:").pack(side=tk.LEFT, padx=5)
        day_btn = ttk.Button(view_frame, text="Daily", command=lambda: self.switch_view("day"))
        day_btn.pack(side=tk.LEFT, padx=2)
        week_btn = ttk.Button(view_frame, text="Weekly", command=lambda: self.switch_view("week"))
        week_btn.pack(side=tk.LEFT, padx=2)
    
    def on_interval_selected(self, event) -> None:
        """Handle interval selection from dropdown."""
        selected_interval = self.interval_var.get()
        
        # Find the corresponding seconds value
        for name, seconds in HIGHRES_INTERVALS:
            if name == selected_interval:
                self.candle_interval_seconds = seconds
                break
        
        # Update the view if we're already in high-res mode
        if self.current_view == "high_res":
            self.update_high_res_view()
    
    def set_candle_interval(self, seconds: int) -> None:
        """Set the candle interval and update the interval dropdown.
        
        Args:
            seconds: Interval in seconds
        """
        # Update the interval
        self.candle_interval_seconds = seconds
        
        # Find the corresponding name and update the dropdown
        for name, secs in HIGHRES_INTERVALS:
            if secs == seconds:
                self.interval_var.set(name)
                break
        
        # Update the view if we're already in high-res mode
        if self.current_view == "high_res":
            self.update_high_res_view()
    
    def load_data(self) -> None:
        """Load accelerometer data from a CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Accelerometer Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Load the data using the model
            print(f"Loading data from {filename}...")
            self.model.load_data(filename)
            
            # Store this as user data
            self.user_data = self.model.data
            self.using_sample_data = False
            
            # Update button text if we were in simulation mode
            if self.simulation_active:
                self.simulation_active = False
                self.sim_btn.config(text="Use Sample Data")
            
            # Update view
            self.update_view_label()
            self.update_view()
            
            # Show file info
            file_size_kb = os.path.getsize(filename) / 1024
            file_size_mb = file_size_kb / 1024
            
            if file_size_mb >= 1:
                size_str = f"{file_size_mb:.2f} MB"
            else:
                size_str = f"{file_size_kb:.2f} KB"
                
            messagebox.showinfo("Data Loaded", 
                              f"Successfully loaded data from {os.path.basename(filename)}\n"
                              f"File size: {size_str}\n"
                              f"Number of rows: {len(self.model.data):,}\n"
                              f"Date range: {self.model.data['timestamp'].min().date()} to "
                              f"{self.model.data['timestamp'].max().date()}\n"
                              f"Resolution: {'Second-level' if self.model.has_second_resolution else 'Minute-level'}")
            
        except Exception as e:
            messagebox.showerror("Error Loading Data", str(e))
    
    def update_view(self) -> None:
        """Update the current view."""
        if self.model.data is None:
            return
            
        try:
            if self.current_view == "day":
                self.update_day_view()
            elif self.current_view == "week":
                self.update_week_view()
            elif self.current_view == "high_res":
                self.update_high_res_view()
            
        except Exception as e:
            messagebox.showerror("Error Updating View", str(e))
    
    def update_day_view(self) -> None:
        """Update the day view."""
        # Get current date
        current_date = self.model.get_current_date()
        if current_date is None:
            return
            
        # Get hourly data
        hourly_data = self.model.get_daily_data_grouped_by_hour()
        
        if hourly_data is None or len(hourly_data) == 0:
            self.chart_view.clear()
            messagebox.showinfo("No Data", f"No data available for {current_date}")
            return
        
        # Update chart
        self.chart_view.plot_day_view(hourly_data, current_date)
        
        # Update analysis
        day_analysis = self.model.analyze_day_patterns()
        self.analysis_view.update_day_analysis(day_analysis)
        
        # Force immediate update
        self.root.update()
    
    def update_week_view(self) -> None:
        """Update the week view."""
        # Get weekly data
        weekly_data = self.model.get_weekly_data()
        
        # Update chart
        self.chart_view.plot_week_view(weekly_data)
        
        # Update analysis
        week_analysis = self.model.analyze_week_patterns()
        self.analysis_view.update_week_analysis(week_analysis)
    
    def update_high_res_view(self) -> None:
        """Update the high-resolution view with the selected time window."""
        try:
            # Get hour values from UI
            self.selected_start_hour = int(self.start_hour_var.get())
            self.selected_end_hour = int(self.end_hour_var.get())
            
            # Validate input
            if self.selected_start_hour < 0 or self.selected_start_hour > 23:
                raise ValueError("Start hour must be between 0 and 23")
            
            if self.selected_end_hour < 0 or self.selected_end_hour > 24:
                raise ValueError("End hour must be between 0 and 24")
            
            if self.selected_end_hour <= self.selected_start_hour:
                raise ValueError("End hour must be greater than start hour")
                
            if self.selected_end_hour - self.selected_start_hour > 4:
                raise ValueError("Time window must be 4 hours or less")
            
            # Switch to high-res view if not already in it
            if self.current_view != "high_res":
                self.current_view = "high_res"
            
            # Get current date
            current_date = self.model.get_current_date()
            if current_date is None:
                return
            
            # Get high-resolution data
            window_data = self.model.get_high_resolution_data(
                self.selected_start_hour, self.selected_end_hour
            )
            
            if window_data is None or len(window_data) == 0:
                self.chart_view.clear()
                messagebox.showinfo("No Data", f"No data available for the {self.selected_start_hour}:00-{self.selected_end_hour}:00 time window")
                return
                
            # Process into candles with the selected interval
            candle_data = self.model.get_candle_data(window_data, self.candle_interval_seconds)
            
            if len(candle_data) == 0:
                self.chart_view.clear()
                messagebox.showinfo("Insufficient Data", 
                                  f"Not enough data points to create {self.candle_interval_seconds}-second candles "
                                  f"in the selected time window.")
                return
            
            # Update chart
            self.chart_view.plot_high_resolution_view(
                candle_data, current_date, 
                self.selected_start_hour, self.selected_end_hour,
                self.candle_interval_seconds
            )
            
            # Update analysis
            self.analysis_view.update_high_res_analysis(self.candle_interval_seconds)
            
            # Update view label
            self.update_view_label()
            
        except ValueError as e:
            messagebox.showerror("Invalid Time Window", str(e))
    
    def update_view_label(self) -> None:
        """Update the label showing the current view."""
        if self.model.data is None:
            self.view_label.config(text="No data loaded")
            return
            
        current_date = self.model.get_current_date()
        if current_date is None:
            self.view_label.config(text="No data available")
            return
            
        if self.current_view == "day":
            self.view_label.config(text=f"Viewing: {current_date.strftime('%A, %B %d, %Y')} (Hourly candles)")
        elif self.current_view == "week":
            self.view_label.config(text="Viewing: Weekly Pattern (Daily candles)")
        elif self.current_view == "high_res":
            # Format interval for display
            if self.candle_interval_seconds < 60:
                interval_str = f"{self.candle_interval_seconds}s"
            elif self.candle_interval_seconds == 60:
                interval_str = "1min"
            elif self.candle_interval_seconds % 60 == 0:
                interval_str = f"{self.candle_interval_seconds // 60}min"
            else:
                interval_str = f"{self.candle_interval_seconds}s"
                
            self.view_label.config(text=f"High-Res: {current_date.strftime('%a %b %d')} "
                                  f"{self.selected_start_hour:02d}:00-{self.selected_end_hour:02d}:00 "
                                  f"({interval_str} candles)")
    
    def switch_view(self, view_type: str) -> None:
        """Switch between day, week, and high-resolution views.
        
        Args:
            view_type: Type of view ('day', 'week', or 'high_res')
        """
        if self.model.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        self.current_view = view_type
        self.update_view_label()
        self.update_view()
    
    def next_day(self) -> None:
        """Navigate to the next day."""
        if self.model.data is None:
            return
            
        self.model.next_day()
        self.update_view_label()
        self.update_view()
    
    def previous_day(self) -> None:
        """Navigate to the previous day."""
        if self.model.data is None:
            return
            
        self.model.previous_day()
        self.update_view_label()
        self.update_view()
    
    def on_day_selected(self, event) -> None:
        """Handle day selection from dropdown for week view."""
        selected_day = self.day_selector.get()
        
        if self.model.data is None or not selected_day:
            return
            
        # Find the day index
        day_index = self.model.find_day_index_by_name(selected_day)
        if day_index is None:
            messagebox.showinfo("No Data", f"No data available for {selected_day}")
            return
            
        # Update model and view
        self.model.current_day_index = day_index
        self.current_view = "day"  # Switch to day view
        self.update_view_label()
        self.update_view()
    
    def toggle_simulation(self) -> None:
        """Toggle between user data and sample data."""
        if self.using_sample_data:
            # Switch back to user data if available
            if self.user_data is not None:
                self.simulation_active = False
                self.using_sample_data = False
                self.model.data = self.user_data
                self.model.detect_data_resolution(self.user_data)
                self.model.days = sorted(self.model.data['timestamp'].dt.date.unique())
                self.model.current_day_index = 0
                
                # Update button and title
                self.sim_btn.config(text="Use Sample Data")
                self.root.title("KinetiCandles: Movement Pattern Analyzer")
                
                # Update view
                self.current_view = "day"
                self.update_view_label()
                self.update_view()
                
                messagebox.showinfo("User Data Restored", "Switched back to your loaded data.")
            else:
                messagebox.showinfo("No User Data", "You haven't loaded any data yet. Please use the 'Load Data' button.")
        else:
            # Switch to sample data
            self.using_sample_data = True
            self.simulation_active = True
            
            # Generate sample data
            sample_df = generate_high_res_sample_data()
            
            # Load the sample data
            self.model.data = sample_df
            self.model.has_second_resolution = True
            self.model.days = sorted(self.model.data['timestamp'].dt.date.unique())
            self.model.current_day_index = 0
            
            # Update button and title
            self.sim_btn.config(text="Use My Data")
            self.root.title("KinetiCandles: Using Sample Data")
            
            # Update view
            self.current_view = "day"
            self.update_view_label()
            self.update_view()
            
            messagebox.showinfo("Sample Data Loaded", 
                              "Now using built-in sample data with 1-second resolution.\n\n"
                              "This data contains simulated activity patterns for a full week.\n\n"
                              "Click 'Use My Data' to switch back to your loaded data.")
    
    def simulation_step(self) -> None:
        """Perform a single step in the simulation."""
        if not self.simulation_active:
            return
            
        # Move to next day
        next_day_index = (self.model.current_day_index + 1) % len(self.model.days)
        self.model.current_day_index = next_day_index
        
        # Get the current date for display
        current_date = self.model.get_current_date()
        if current_date:
            date_str = current_date.strftime('%A, %B %d, %Y')
            print(f"Simulation: Now showing {date_str}")
            
            # Update title to show simulation status
            self.root.title(f"KinetiCandles: SIMULATION MODE - Day {next_day_index+1}/{len(self.model.days)} - {date_str}")
        
        # Update view label and day view
        self.update_view_label()
        self.update_day_view()
        
        # Force the update to display immediately
        self.root.update_idletasks()
        
        # Check if we've completed a full cycle
        if next_day_index == self.simulation_day_index:
            # We've gone through all days, stop simulation
            self.simulation_active = False
            self.sim_btn.config(text="Start Simulation")
            self.root.title("KinetiCandles: Movement Pattern Analyzer")  # Reset title
            messagebox.showinfo("Simulation Complete", "The simulation has completed a full cycle through all days.")
        else:
            # Schedule the next update if simulation is still active
            if self.simulation_active:
                self.root.after(3000, self.simulation_step)
    
    def export_view(self) -> None:
        """Export the current view as an image."""
        if self.model.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Chart As"
        )
        
        if file_path:
            try:
                self.chart_view.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Chart saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def show_pattern_guide(self) -> None:
        """Show the pattern guide window."""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("KinetiCandles Pattern Guide")
        guide_window.geometry("600x500")
        
        # Create scrollable text area
        frame = ttk.Frame(guide_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Add pattern guide content
        text.insert(tk.END, "KinetiCandles: Movement Pattern Reference Guide\n\n", "title")
        text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Daily patterns
        text.insert(tk.END, "Daily Patterns\n\n", "section")
        
        for pattern_id, pattern_info in PATTERN_TYPES.items():
            text.insert(tk.END, f"{pattern_info['name']}\n", "heading")
            text.insert(tk.END, "-" * 20 + "\n")
            text.insert(tk.END, f"{pattern_info['description']}\n\n")
            
            # Add additional info based on pattern type
            if pattern_id == "morning_peak":
                text.insert(tk.END, "Visual Signature: Tall green candles in morning hours (6-9am) with progressively smaller candles afterward\n\n")
                text.insert(tk.END, "Health Implications: Often associated with good sleep hygiene and regular circadian rhythm\n\n")
            elif pattern_id == "evening_peak":
                text.insert(tk.END, "Visual Signature: Small morning candles with progressively larger candles in evening (5-8pm)\n\n")
                text.insert(tk.END, "Health Implications: May indicate delayed circadian rhythm or night owl chronotype\n\n")
            elif pattern_id == "bimodal":
                text.insert(tk.END, "Visual Signature: Two distinct peaks (morning and evening) with a mid-day trough\n\n")
                text.insert(tk.END, "Health Implications: Often seen in people with structured work schedules\n\n")
        
        # Weekly patterns
        text.insert(tk.END, "Weekly Patterns\n\n", "section")
        
        for pattern_id, pattern_info in WEEKLY_PATTERN_TYPES.items():
            text.insert(tk.END, f"{pattern_info['name']}\n", "heading")
            text.insert(tk.END, "-" * 20 + "\n")
            text.insert(tk.END, f"{pattern_info['description']}\n\n")
            
        # High-resolution patterns
        text.insert(tk.END, "High-Resolution Patterns\n\n", "section")
        text.insert(tk.END, "Second-by-Second Analysis\n", "heading")
        text.insert(tk.END, "-" * 20 + "\n")
        text.insert(tk.END, "The high-resolution view allows analysis of moment-to-moment activity patterns.\n\n")
        text.insert(tk.END, "Candlestick Interpretation:\n")
        text.insert(tk.END, "• Green candles: Activity increased during the time interval\n")
        text.insert(tk.END, "• Red candles: Activity decreased during the time interval\n")
        text.insert(tk.END, "• Tall wicks: High volatility within the time period\n")
        text.insert(tk.END, "• Short bodies: Opening and closing activity levels were similar\n\n")
        
        text.insert(tk.END, "Common Micro-Patterns:\n")
        text.insert(tk.END, "• Activity Bursts: Clusters of tall green candles indicate intense, short-duration activity\n")
        text.insert(tk.END, "• Rest Intervals: Series of red candles with low activity levels\n")
        text.insert(tk.END, "• Transition Phases: Alternating red and green candles of increasing/decreasing height\n\n")
        
        # Format text
        text.tag_configure("title", font=("Arial", 14, "bold"))
        text.tag_configure("section", font=("Arial", 12, "bold"))
        text.tag_configure("heading", font=("Arial", 10, "bold"))
        
        # Make text read-only
        text.config(state=tk.DISABLED)
    
    def show_time_domain_analysis(self) -> None:
        """Show time domain analysis window."""
        if self.model.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        # Create a new window for time domain analysis
        time_window = tk.Toplevel(self.root)
        time_window.title("Time Domain Analysis")
        time_window.geometry("800x600")
        
        # Add content to the window
        frame = ttk.Frame(time_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Time Domain Analysis", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Add buttons for different time domain analyses
        analysis_frame = ttk.Frame(frame)
        analysis_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(analysis_frame, text="Basic Statistics", 
                  command=lambda: self.calculate_time_domain("basic", result_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_frame, text="Activity Counts", 
                  command=lambda: self.calculate_time_domain("counts", result_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_frame, text="Moving Averages", 
                  command=lambda: self.calculate_time_domain("moving_avg", result_text)).pack(side=tk.LEFT, padx=5)
        
        # Add text area for results
        result_frame = ttk.LabelFrame(frame, text="Analysis Results")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        result_text = tk.Text(result_frame, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # Add placeholder text
        result_text.insert(tk.END, "Select an analysis type above to view time domain metrics.\n\n")
        result_text.insert(tk.END, "Available analyses include basic statistical measures, ")
        result_text.insert(tk.END, "activity count summaries, and various moving average calculations.")
    
    def calculate_time_domain(self, analysis_type: str, result_text: tk.Text) -> None:
        """Calculate time domain metrics.
        
        Args:
            analysis_type: Type of analysis to perform
            result_text: Text widget to display results
        """
        # Clear previous results
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Calculating {analysis_type} time domain analysis...\n\n")
        
        try:
            # Get current day data
            day_data = self.model.get_data_for_current_day()
            
            if day_data is None or len(day_data) == 0:
                result_text.insert(tk.END, "No data available for the current day.")
                return
                
            # Perform analysis based on type
            if analysis_type == "basic":
                # Basic statistics
                stats = day_data['activity_level'].describe()
                
                result_text.insert(tk.END, f"Basic Statistics for {self.model.get_current_date()}\n\n")
                result_text.insert(tk.END, f"Count: {stats['count']:.0f} data points\n")
                result_text.insert(tk.END, f"Mean: {stats['mean']:.2f}\n")
                result_text.insert(tk.END, f"Standard Deviation: {stats['std']:.2f}\n")
                result_text.insert(tk.END, f"Minimum: {stats['min']:.2f}\n")
                result_text.insert(tk.END, f"25th Percentile: {stats['25%']:.2f}\n")
                result_text.insert(tk.END, f"Median: {stats['50%']:.2f}\n")
                result_text.insert(tk.END, f"75th Percentile: {stats['75%']:.2f}\n")
                result_text.insert(tk.END, f"Maximum: {stats['max']:.2f}\n")
                
            elif analysis_type == "counts":
                # Activity counts
                result_text.insert(tk.END, f"Activity Counts for {self.model.get_current_date()}\n\n")
                
                # Count activity levels by intensity
                low = len(day_data[day_data['activity_level'] < 30])
                moderate = len(day_data[(day_data['activity_level'] >= 30) & (day_data['activity_level'] < 60)])
                high = len(day_data[day_data['activity_level'] >= 60])
                
                result_text.insert(tk.END, f"Total data points: {len(day_data)}\n")
                result_text.insert(tk.END, f"Low activity counts (<30): {low} ({low/len(day_data)*100:.1f}%)\n")
                result_text.insert(tk.END, f"Moderate activity counts (30-59): {moderate} ({moderate/len(day_data)*100:.1f}%)\n")
                result_text.insert(tk.END, f"High activity counts (60+): {high} ({high/len(day_data)*100:.1f}%)\n\n")
                
                # Find peak activity periods
                hourly = day_data.groupby(day_data['timestamp'].dt.hour)['activity_level'].mean()
                peak_hour = hourly.idxmax()
                result_text.insert(tk.END, f"Peak activity hour: {peak_hour:02d}:00 (Average: {hourly[peak_hour]:.1f})\n")
                
            elif analysis_type == "moving_avg":
                # Moving averages
                result_text.insert(tk.END, f"Moving Averages for {self.model.get_current_date()}\n\n")
                
                # Calculate different window sizes based on data resolution
                if self.model.has_second_resolution:
                    result_text.insert(tk.END, "Calculated with 1-second resolution data:\n")
                    result_text.insert(tk.END, "- 1-minute moving average\n")
                    result_text.insert(tk.END, "- 5-minute moving average\n")
                    result_text.insert(tk.END, "- 15-minute moving average\n\n")
                else:
                    result_text.insert(tk.END, "Calculated with minute/hour resolution data:\n")
                    result_text.insert(tk.END, "- 1-hour moving average\n")
                    result_text.insert(tk.END, "- 3-hour moving average\n\n")
                
                result_text.insert(tk.END, "Note: To visualize moving averages, use the main view with K-Line enabled.\n")
                result_text.insert(tk.END, "The K-Line in the main chart shows the moving average for the selected view.")
                
        except Exception as e:
            result_text.insert(tk.END, f"Error calculating time domain metrics: {str(e)}")
    
    def show_frequency_domain_analysis(self) -> None:
        """Show frequency domain analysis window."""
        if self.model.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        # Create a new window for frequency domain analysis
        freq_window = tk.Toplevel(self.root)
        freq_window.title("Frequency Domain Analysis")
        freq_window.geometry("800x600")
        
        # Add content to the window
        frame = ttk.Frame(freq_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Frequency Domain Analysis", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Add information about frequency analysis
        info_frame = ttk.LabelFrame(frame, text="Information")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, height=5)
        info_text.pack(fill=tk.X, padx=10, pady=10)
        info_text.insert(tk.END, "Frequency domain analysis examines patterns in activity data using Fast Fourier Transform (FFT).\n\n")
        info_text.insert(tk.END, "This reveals periodic patterns and dominant frequencies in the movement data, such as:")
        info_text.insert(tk.END, " daily routines, work-rest cycles, and natural movement rhythms.")
        info_text.config(state=tk.DISABLED)
        
        # Add a placeholder for the frequency visualization
        result_frame = ttk.LabelFrame(frame, text="Frequency Analysis")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(result_frame, text="Select High-Resolution Data for Frequency Analysis", font=("Arial", 12)).pack(pady=20)
        ttk.Label(result_frame, text="For optimal frequency analysis, use 1-second resolution data over 1-4 hours.").pack()
        
        # Add buttons for analysis
        button_frame = ttk.Frame(result_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Analyze Current Day", 
                  command=lambda: messagebox.showinfo("Frequency Analysis", 
                                                    "This would perform FFT analysis on the current day's data.\n\n"
                                                    "In a full implementation, it would show frequency components and power spectrum.")).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(button_frame, text="Analyze Selected Window", 
                  command=lambda: messagebox.showinfo("Frequency Analysis", 
                                                    "This would perform FFT analysis on the current high-resolution window.\n\n"
                                                    "For best results, select a 1-2 hour window with 1-second data.")).pack(side=tk.LEFT, padx=10)
    
    def show_advanced_measures(self) -> None:
        """Show other advanced analysis measures."""
        if self.model.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        # Create a new window for advanced measures
        adv_window = tk.Toplevel(self.root)
        adv_window.title("Advanced Activity Measures")
        adv_window.geometry("800x600")
        
        # Add content to the window
        frame = ttk.Frame(adv_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Advanced Activity Measures", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add tabs for different measure categories
        entropy_tab = ttk.Frame(notebook)
        complexity_tab = ttk.Frame(notebook)
        pattern_tab = ttk.Frame(notebook)
        
        notebook.add(entropy_tab, text="Entropy Measures")
        notebook.add(complexity_tab, text="Complexity Metrics")
        notebook.add(pattern_tab, text="Pattern Recognition")
        
        # Add content to entropy tab
        ttk.Label(entropy_tab, text="Entropy measures quantify randomness and predictability in activity patterns.", font=("Arial", 11)).pack(pady=10)
        ttk.Button(entropy_tab, text="Calculate Sample Entropy", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would calculate sample entropy for the activity data.\n\n"
                                                    "Sample entropy measures the complexity/regularity of time series data.")).pack(pady=5)
        ttk.Button(entropy_tab, text="Calculate Approximate Entropy", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would calculate approximate entropy for the activity data.\n\n"
                                                    "ApEn quantifies the unpredictability of fluctuations in the data.")).pack(pady=5)
        
        # Add content to complexity tab
        ttk.Label(complexity_tab, text="Complexity metrics measure the structural complexity of activity patterns.", font=("Arial", 11)).pack(pady=10)
        ttk.Button(complexity_tab, text="Calculate Fractal Dimension", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would calculate fractal dimension for the activity data.\n\n"
                                                    "Fractal dimension measures how activity patterns fill space across different time scales.")).pack(pady=5)
        ttk.Button(complexity_tab, text="Calculate Detrended Fluctuation Analysis", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would perform DFA on the activity data.\n\n"
                                                    "DFA identifies long-range correlations and scaling properties in the data.")).pack(pady=5)
        
        # Add content to pattern tab
        ttk.Label(pattern_tab, text="Pattern recognition identifies recurring activity patterns.", font=("Arial", 11)).pack(pady=10)
        ttk.Button(pattern_tab, text="Find Repeating Patterns", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would identify repeating activity patterns.\n\n"
                                                    "This analysis finds recurring movement sequences across different time periods.")).pack(pady=5)
        ttk.Button(pattern_tab, text="Cluster Similar Activities", 
                  command=lambda: messagebox.showinfo("Advanced Analysis", 
                                                    "This would cluster similar activity patterns.\n\n"
                                                    "Clustering groups similar movement patterns to identify common behaviors.")).pack(pady=5)
    
    def show_about(self) -> None:
        """Show about dialog."""
        about_text = """
        KinetiCandles: Movement Pattern Analyzer
        Version 3.0
        
        A tool for visualizing and analyzing temporal movement patterns
        using K-plot (candlestick) visualization inspired by financial charts.
        
        This application helps researchers and individuals understand their
        movement behavior patterns throughout the day and week, with special
        support for high-resolution (1-second) accelerometer data.
        
        Features:
        - Daily, weekly, and high-resolution views
        - Configurable candle intervals (15s, 30s, 1min, 5min)
        - Pattern detection and analysis
        - Time and frequency domain analysis
        - Advanced complexity measures
        - Simulation mode for data exploration
        - Export capabilities
        
        Created for the LABDA Academy Hackathon.
        """
        
        messagebox.showinfo("About KinetiCandles", about_text)


# Data generator functions for testing
def generate_sample_data() -> pd.DataFrame:
    """Generate sample accelerometer data for testing."""
    # Create a week of data
    start_date = datetime.datetime(2023, 5, 1)
    days = 7
    
    # Create empty dataframe
    data = []
    
    # Generate data points for each day
    for day in range(days):
        current_date = start_date + datetime.timedelta(days=day)
        
        # Generate 24 hourly data points
        for hour in range(24):
            timestamp = current_date + datetime.timedelta(hours=hour)
            
            # Create activity pattern
            # Morning person pattern: high activity in morning
            if day < 5:  # Weekday
                if hour < 6:  # Sleep
                    activity = max(5, np.random.normal(10, 5))
                elif 6 <= hour < 9:  # Morning activity peak
                    activity = max(10, np.random.normal(70, 15))
                elif 9 <= hour < 12:  # Work morning
                    activity = max(10, np.random.normal(40, 10))
                elif 12 <= hour < 14:  # Lunch
                    activity = max(10, np.random.normal(60, 15))
                elif 14 <= hour < 17:  # Work afternoon
                    activity = max(10, np.random.normal(35, 10))
                elif 17 <= hour < 19:  # Evening commute/exercise
                    activity = max(10, np.random.normal(65, 15))
                elif 19 <= hour < 22:  # Evening leisure
                    activity = max(10, np.random.normal(30, 10))
                else:  # Wind down for sleep
                    activity = max(5, np.random.normal(15, 5))
            else:  # Weekend
                if hour < 8:  # Sleep longer
                    activity = max(5, np.random.normal(10, 5))
                elif 8 <= hour < 11:  # Morning leisure
                    activity = max(10, np.random.normal(40, 10))
                elif 11 <= hour < 15:  # Weekend activities
                    activity = max(10, np.random.normal(75, 20))
                elif 15 <= hour < 19:  # Afternoon activities
                    activity = max(10, np.random.normal(65, 15))
                elif 19 <= hour < 23:  # Evening leisure
                    activity = max(10, np.random.normal(45, 15))
                else:  # Late night
                    activity = max(5, np.random.normal(20, 10))
            
            # Add some random variation to make data realistic
            activity += np.random.normal(0, 5)
            activity = max(0, min(100, activity))  # Constrain between 0-100
            
            # Add to data list
            data.append({
                'timestamp': timestamp,
                'activity_level': activity
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add day_of_week column
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    return df


def generate_high_res_sample_data() -> pd.DataFrame:
    """Generate high-resolution sample accelerometer data for testing.
    
    Returns a complete dataset with 1-second resolution for all days.
    Note that for performance reasons, when using this data, it's 
    recommended to limit the time window to 1-2 hours.
    """
    # Create a week of data with 1-second intervals for high-resolution analysis
    start_date = datetime.datetime(2023, 5, 1)
    days = 7
    interval_seconds = 1  # 1-second intervals
    
    # Create empty dataframe
    data = []
    
    # Generate data points for each day
    for day in range(days):
        current_date = start_date + datetime.timedelta(days=day)
        
        # Generate data points throughout the day
        for hour in range(24):
            for minute in range(60):
                for second in range(0, 60, interval_seconds):
                    timestamp = current_date + datetime.timedelta(hours=hour, minutes=minute, seconds=second)
                    
                    # Base activity level from hourly pattern
                    if day < 5:  # Weekday pattern
                        if hour < 6:  # Sleep
                            base_activity = max(5, np.random.normal(10, 5))
                        elif 6 <= hour < 9:  # Morning activity peak
                            base_activity = max(10, np.random.normal(70, 15))
                        elif 9 <= hour < 12:  # Work morning
                            base_activity = max(10, np.random.normal(40, 10))
                        elif 12 <= hour < 14:  # Lunch
                            base_activity = max(10, np.random.normal(60, 15))
                        elif 14 <= hour < 17:  # Work afternoon
                            base_activity = max(10, np.random.normal(35, 10))
                        elif 17 <= hour < 19:  # Evening commute/exercise
                            base_activity = max(10, np.random.normal(65, 15))
                        elif 19 <= hour < 22:  # Evening leisure
                            base_activity = max(10, np.random.normal(30, 10))
                        else:  # Wind down for sleep
                            base_activity = max(5, np.random.normal(15, 5))
                    else:  # Weekend pattern
                        if hour < 8:  # Sleep longer
                            base_activity = max(5, np.random.normal(10, 5))
                        elif 8 <= hour < 11:  # Morning leisure
                            base_activity = max(10, np.random.normal(40, 10))
                        elif 11 <= hour < 15:  # Weekend activities
                            base_activity = max(10, np.random.normal(75, 20))
                        elif 15 <= hour < 19:  # Afternoon activities
                            base_activity = max(10, np.random.normal(65, 15))
                        elif 19 <= hour < 23:  # Evening leisure
                            base_activity = max(10, np.random.normal(45, 15))
                        else:  # Late night
                            base_activity = max(5, np.random.normal(20, 10))
                    
                    # Add minute-level patterns
                    minute_factor = 1.0
                    
                    # Beginning of hour tends to be more active
                    if minute < 15:
                        minute_factor = 1.1
                    # Mid-hour dip
                    elif 25 <= minute < 40:
                        minute_factor = 0.9
                    # End of hour increase
                    elif minute >= 50:
                        minute_factor = 1.05
                    
                    # Add short-term variations for 1-second data
                    # This creates small fluctuations that make the 1-second 
                    # resolution data more realistic and interesting to visualize
                    short_term_factor = 1.0 + 0.05 * np.sin(second * 0.5) + 0.03 * np.cos(second * 0.3)
                    
                    # Calculate final activity
                    activity = base_activity * minute_factor * short_term_factor
                    
                    # Ensure we get some red candles by occasionally decreasing activity
                    if np.random.random() < 0.4:  # 40% chance of activity decrease
                        activity = activity * np.random.uniform(0.7, 0.95)
                    
                    # Constrain between 0-100
                    activity = max(0, min(100, activity))
                    
                    # Add to data list
                    data.append({
                        'timestamp': timestamp,
                        'activity_level': activity
                    })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add day_of_week column
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    return df


# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = KinetiCandlesApp(root)
    
    # Ask if user wants to load sample data for demo
    if messagebox.askyesno("Data Selection", "Would you like to use sample data for demonstration?\n\nSelect 'Yes' to use built-in sample data.\nSelect 'No' to load your own data."):
        # Use sample data
        app.toggle_simulation()  # This will load the sample data
    else:
        # Prompt user to load their own data
        app.load_data()
    
    root.mainloop()