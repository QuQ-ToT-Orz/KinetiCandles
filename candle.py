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

class KinetiCandlesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KinetiCandles: Movement Pattern Analyzer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Data storage
        self.data = None
        self.current_view = "day"  # 'day', 'week', or 'high_res'
        self.current_day = 0
        self.simulation_active = False
        self.simulation_thread = None
        
        # Default time window for high-resolution view
        self.selected_start_hour = 8
        self.selected_end_hour = 10
        
        # Create UI
        self.create_menu()
        self.create_main_frame()
        
    def create_menu(self):
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
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Pattern Guide", command=self.show_pattern_guide)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_frame(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control panel
        self.control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # Create a row for buttons
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Load data button
        load_btn = ttk.Button(button_frame, text="Load Data", command=self.load_data)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Simulation controls
        self.sim_btn = ttk.Button(button_frame, text="Start Simulation", command=self.toggle_simulation)
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
        self.day_selector = ttk.Combobox(button_frame, values=["Monday", "Tuesday", "Wednesday", 
                                                          "Thursday", "Friday", "Saturday", "Sunday"])
        self.day_selector.pack(side=tk.RIGHT, padx=5)
        self.day_selector.bind("<<ComboboxSelected>>", self.on_day_selected)
        
        # High-resolution time window selectors
        self.add_time_window_selector()
        
        # Create matplotlib figure for the K-plot
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Embed matplotlib figure in tkinter
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Pattern detection and analysis panel
        analysis_frame = ttk.LabelFrame(main_frame, text="Pattern Analysis", padding="10")
        analysis_frame.pack(fill=tk.X, pady=5)
        
        # Text widget for analysis results
        self.analysis_text = tk.Text(analysis_frame, height=8, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        self.analysis_text.insert(tk.END, "Load data to see movement pattern analysis...")
        self.analysis_text.config(state=tk.DISABLED)
    
    def add_time_window_selector(self):
        """Add time window selector for high-resolution view"""
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
        
        # Apply button
        apply_btn = ttk.Button(time_frame, text="Apply", command=self.update_high_res_view)
        apply_btn.pack(side=tk.LEFT, padx=10)
        
        # High-resolution view button
        hi_res_btn = ttk.Button(time_frame, text="Minute-by-Minute View", 
                               command=lambda: self.switch_view("high_res"))
        hi_res_btn.pack(side=tk.LEFT, padx=10)
    
    def load_data(self):
        """Load accelerometer data from a CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Accelerometer Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Load the data
            self.data = pd.read_csv(filename)
            
            # Check for required columns
            required_columns = ['timestamp', 'activity_level']
            if not all(col in self.data.columns for col in required_columns):
                messagebox.showerror("Invalid Data Format", 
                                    f"The file must contain these columns: {', '.join(required_columns)}")
                return
            
            # Convert timestamp to datetime
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            # Add day of week
            self.data['day_of_week'] = self.data['timestamp'].dt.day_name()
            
            # Initialize view to first day
            self.current_day = 0
            self.update_view_label()
            
            # Plot the data
            self.plot_kcandles()
            
            # Update analysis
            self.analyze_patterns()
            
        except Exception as e:
            messagebox.showerror("Error Loading Data", str(e))
    
    def plot_kcandles(self):
        """Plot K-candles (candlestick) chart for the activity data"""
        if self.data is None:
            return
        
        # Clear previous plot
        self.ax.clear()
        
        try:
            if self.current_view == "day":
                self.plot_day_view()
            elif self.current_view == "week":
                self.plot_week_view()
            elif self.current_view == "high_res":
                self.plot_high_resolution_view()
            
            # Add grid and labels
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Activity Level')
            
            # Refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error Plotting Data", str(e))
    
    def plot_day_view(self):
        """Plot K-candles for a single day"""
        # Get data for current day
        days = sorted(self.data['timestamp'].dt.date.unique())
        
        if not days:
            return
        
        # Make sure current_day is valid
        if self.current_day >= len(days):
            self.current_day = 0
        
        selected_date = days[self.current_day]
        day_data = self.data[self.data['timestamp'].dt.date == selected_date]
        
        # Group by hour for K-candles
        hourly_data = day_data.groupby(day_data['timestamp'].dt.hour)['activity_level'].agg([
            'first', 'last', 'max', 'min'
        ]).reset_index()
        
        # Plot K-candles
        hours = hourly_data['timestamp']
        self.ax.set_title(f"Movement Patterns: {selected_date.strftime('%A, %B %d, %Y')}")
        
        # X-axis limits and labels
        self.ax.set_xlim(-0.5, 23.5)
        self.ax.set_xticks(range(0, 24, 2))
        self.ax.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)])
        
        # Plot each candle
        for i, hour in enumerate(hours):
            # Candle data
            open_val = hourly_data.loc[i, 'first']
            close_val = hourly_data.loc[i, 'last']
            high_val = hourly_data.loc[i, 'max']
            low_val = hourly_data.loc[i, 'min']
            
            # Determine color based on open vs close
            color = 'green' if close_val >= open_val else 'red'
            
            # Plot high-low line
            self.ax.plot([hour, hour], [low_val, high_val], color='black', linewidth=1)
            
            # Plot candle body
            width = 0.8
            rect = plt.Rectangle((hour - width/2, min(open_val, close_val)), 
                                width, abs(open_val - close_val),
                                fill=True, color=color, alpha=0.6)
            self.ax.add_patch(rect)
        
        # Add moving average line (K-line)
        if len(hourly_data) >= 3:  # Need at least 3 points for meaningful average
            ma_data = hourly_data['last'].rolling(window=3, min_periods=1).mean()
            self.ax.plot(hours, ma_data, color='purple', linewidth=2, label='K-Line (3-hour MA)')
            self.ax.legend()
    
    def plot_week_view(self):
        """Plot K-candles for a full week"""
        # Get unique days of the week
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Set up plot
        self.ax.set_title("Weekly Movement Patterns")
        self.ax.set_xlim(-0.5, 6.5)
        self.ax.set_xticks(range(7))
        self.ax.set_xticklabels(days_of_week)
        
        # Process data for each day of the week
        for i, day in enumerate(days_of_week):
            day_data = self.data[self.data['day_of_week'] == day]
            
            if len(day_data) == 0:
                continue
                
            # Calculate open, close, high, low for the day
            open_val = day_data.iloc[0]['activity_level']
            close_val = day_data.iloc[-1]['activity_level']
            high_val = day_data['activity_level'].max()
            low_val = day_data['activity_level'].min()
            
            # Determine color based on open vs close
            color = 'green' if close_val >= open_val else 'red'
            
            # Plot high-low line
            self.ax.plot([i, i], [low_val, high_val], color='black', linewidth=1)
            
            # Plot candle body
            width = 0.8
            rect = plt.Rectangle((i - width/2, min(open_val, close_val)), 
                                width, abs(open_val - close_val),
                                fill=True, color=color, alpha=0.6)
            self.ax.add_patch(rect)
    
    def plot_high_resolution_view(self):
        """Plot K-candles with minute-by-minute resolution for a selected time window"""
        if self.data is None:
            return
            
        # Get data for current day
        days = sorted(self.data['timestamp'].dt.date.unique())
        
        if not days:
            return
        
        # Make sure current_day is valid
        if self.current_day >= len(days):
            self.current_day = 0
        
        selected_date = days[self.current_day]
        day_data = self.data[self.data['timestamp'].dt.date == selected_date]
        
        # Filter to a 2-hour window for minute-by-minute resolution
        start_hour = self.selected_start_hour
        end_hour = self.selected_end_hour
        
        window_data = day_data[
            (day_data['timestamp'].dt.hour >= start_hour) & 
            (day_data['timestamp'].dt.hour < end_hour)
        ]
        
        if len(window_data) == 0:
            self.ax.text(0.5, 0.5, "No data available for selected time window", 
                         ha='center', va='center', transform=self.ax.transAxes)
            return
        
        # Group by minute for high-resolution K-candles
        window_data['minute_index'] = window_data['timestamp'].dt.hour * 60 + window_data['timestamp'].dt.minute
        
        # For each minute, calculate open, close, high, low
        # This requires data at sub-minute resolution
        minute_groups = window_data.groupby('minute_index')
        
        minute_data = []
        for minute, group in minute_groups:
            if len(group) > 1:  # Need at least 2 points to form a candle
                minute_data.append({
                    'minute_index': minute,
                    'first': group['activity_level'].iloc[0],
                    'last': group['activity_level'].iloc[-1],
                    'max': group['activity_level'].max(),
                    'min': group['activity_level'].min(),
                    'time_str': f"{minute // 60:02d}:{minute % 60:02d}"
                })
        
        minute_data = pd.DataFrame(minute_data)
        
        if len(minute_data) == 0:
            self.ax.text(0.5, 0.5, "Insufficient resolution for minute-by-minute analysis", 
                         ha='center', va='center', transform=self.ax.transAxes)
            return
        
        # Plot setup
        self.ax.clear()
        self.ax.set_title(f"High-Resolution Movement Pattern: {selected_date.strftime('%A, %B %d, %Y')} "
                         f"{start_hour}:00 - {end_hour}:00")
        
        # X-axis setup - show every 10 minutes
        all_minutes = minute_data['minute_index'].values
        x_ticks = [m for m in all_minutes if m % 10 == 0]
        x_labels = [f"{m // 60:02d}:{m % 60:02d}" for m in x_ticks]
        
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(x_labels, rotation=45)
        
        # Y-axis setup
        self.ax.set_ylabel('Activity Level')
        
        # Plot each minute candle
        for _, row in minute_data.iterrows():
            minute = row['minute_index']
            open_val = row['first']
            close_val = row['last']
            high_val = row['max']
            low_val = row['min']
            
            # Determine color based on open vs close
            color = 'green' if close_val >= open_val else 'red'
            
            # Plot high-low line
            self.ax.plot([minute, minute], [low_val, high_val], color='black', linewidth=1)
            
            # Plot candle body
            width = 0.8
            rect = plt.Rectangle((minute - width/2, min(open_val, close_val)), 
                                width, abs(open_val - close_val),
                                fill=True, color=color, alpha=0.6)
            self.ax.add_patch(rect)
        
        # Add K-line (moving average)
        if len(minute_data) >= 5:  # Need at least 5 points for meaningful average
            window_size = max(5, len(minute_data) // 20)  # Adaptive window size
            ma_data = minute_data['last'].rolling(window=window_size, min_periods=1).mean()
            self.ax.plot(minute_data['minute_index'], ma_data, color='purple', linewidth=2, 
                        label=f'K-Line ({window_size}-min MA)')
            self.ax.legend()
        
        # Add grid for readability
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Set x-axis limits
        if len(all_minutes) > 0:
            self.ax.set_xlim(min(all_minutes) - 2, max(all_minutes) + 2)
    
    def update_view_label(self):
        """Update the label showing the current view"""
        if self.data is None:
            self.view_label.config(text="No data loaded")
            return
            
        if self.current_view == "day":
            days = sorted(self.data['timestamp'].dt.date.unique())
            if days and self.current_day < len(days):
                self.view_label.config(text=f"Viewing: {days[self.current_day].strftime('%A, %B %d, %Y')}")
        elif self.current_view == "week":
            self.view_label.config(text="Viewing: Weekly Pattern")
        elif self.current_view == "high_res":
            days = sorted(self.data['timestamp'].dt.date.unique())
            if days and self.current_day < len(days):
                self.view_label.config(text=f"High-Res: {days[self.current_day].strftime('%a %b %d')} "
                                      f"{self.selected_start_hour}:00 - {self.selected_end_hour}:00")
    
    def switch_view(self, view_type):
        """Switch between day, week, and high-resolution views"""
        if self.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        self.current_view = view_type
        self.update_view_label()
        self.plot_kcandles()
        
        if view_type != "high_res":
            self.analyze_patterns()
        else:
            # Clear analysis for high-res view or perform specialized analysis
            self.analysis_text.config(state=tk.NORMAL)
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, "High-resolution view active. Detailed pattern analysis not available.")
            self.analysis_text.config(state=tk.DISABLED)
    
    def update_high_res_view(self):
        """Update the high-resolution view with selected time window"""
        try:
            self.selected_start_hour = int(self.start_hour_var.get())
            self.selected_end_hour = int(self.end_hour_var.get())
            
            # Validate input
            if self.selected_start_hour < 0 or self.selected_start_hour > 23:
                raise ValueError("Start hour must be between 0 and 23")
            
            if self.selected_end_hour < 0 or self.selected_end_hour > 24:
                raise ValueError("End hour must be between 0 and 24")
            
            if self.selected_end_hour <= self.selected_start_hour or self.selected_end_hour - self.selected_start_hour > 4:
                raise ValueError("Time window must be between 1 and 4 hours")
            
            # Update view if currently in high-res mode
            if self.current_view == "high_res":
                self.update_view_label()
                self.plot_kcandles()
        
        except ValueError as e:
            messagebox.showerror("Invalid Time Window", str(e))
    
    def next_day(self):
        """Navigate to the next day"""
        if self.data is None:
            return
            
        days = sorted(self.data['timestamp'].dt.date.unique())
        if not days:
            return
            
        self.current_day = (self.current_day + 1) % len(days)
        self.update_view_label()
        self.plot_kcandles()
        
        if self.current_view != "high_res":
            self.analyze_patterns()
    
    def previous_day(self):
        """Navigate to the previous day"""
        if self.data is None:
            return
            
        days = sorted(self.data['timestamp'].dt.date.unique())
        if not days:
            return
            
        self.current_day = (self.current_day - 1) % len(days)
        self.update_view_label()
        self.plot_kcandles()
        
        if self.current_view != "high_res":
            self.analyze_patterns()
    
    def on_day_selected(self, event):
        """Handle day selection from dropdown for week view"""
        selected_day = self.day_selector.get()
        
        if self.data is None or not selected_day:
            return
            
        # Find the first occurrence of the selected day
        day_data = self.data[self.data['day_of_week'] == selected_day]
        if len(day_data) == 0:
            messagebox.showinfo("No Data", f"No data available for {selected_day}")
            return
            
        # Get the date of this day
        selected_date = day_data['timestamp'].dt.date.iloc[0]
        
        # Find the index of this date in the unique dates list
        days = sorted(self.data['timestamp'].dt.date.unique())
        try:
            self.current_day = days.index(selected_date)
            self.current_view = "day"  # Switch to day view
            self.update_view_label()
            self.plot_kcandles()
            self.analyze_patterns()
        except ValueError:
            messagebox.showerror("Error", "Could not find the selected day in the data")
    
    def analyze_patterns(self):
        """Analyze movement patterns in the current view"""
        if self.data is None:
            return
            
        # Enable editing of analysis text
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        
        try:
            if self.current_view == "day":
                self.analyze_day_patterns()
            elif self.current_view == "week":
                self.analyze_week_patterns()
        except Exception as e:
            self.analysis_text.insert(tk.END, f"Error analyzing patterns: {str(e)}")
        
        # Disable editing of analysis text
        self.analysis_text.config(state=tk.DISABLED)
    
    def analyze_day_patterns(self):
        """Analyze patterns for a single day"""
        days = sorted(self.data['timestamp'].dt.date.unique())
        if not days or self.current_day >= len(days):
            return
            
        selected_date = days[self.current_day]
        day_data = self.data[self.data['timestamp'].dt.date == selected_date]
        
        # Group by hour for analysis
        hourly_data = day_data.groupby(day_data['timestamp'].dt.hour)['activity_level'].agg([
            'mean', 'std', 'max', 'min'
        ]).reset_index()
        
        # Identify peak activity hours
        peak_hour = hourly_data.loc[hourly_data['max'].idxmax()]['timestamp']
        
        # Calculate activity distribution
        morning_activity = hourly_data[hourly_data['timestamp'].between(6, 11)]['mean'].mean()
        midday_activity = hourly_data[hourly_data['timestamp'].between(12, 17)]['mean'].mean()
        evening_activity = hourly_data[hourly_data['timestamp'].between(18, 23)]['mean'].mean()
        
        # Identify pattern type
        if morning_activity > midday_activity and morning_activity > evening_activity:
            pattern_type = "Morning Peak"
            pattern_desc = "Highest activity in morning hours, gradually decreasing throughout the day."
        elif evening_activity > morning_activity and evening_activity > midday_activity:
            pattern_type = "Evening Peak"
            pattern_desc = "Activity builds throughout the day, reaching highest levels in evening."
        elif midday_activity > morning_activity and midday_activity > evening_activity:
            pattern_type = "Midday Peak"
            pattern_desc = "Activity concentrated during midday hours."
        elif abs(morning_activity - evening_activity) < 5 and morning_activity > midday_activity:
            pattern_type = "Bimodal Pattern"
            pattern_desc = "Two distinct activity peaks (morning and evening) with midday lull."
        else:
            pattern_type = "Consistent Activity"
            pattern_desc = "Relatively consistent activity levels throughout active hours."
        
        # Calculate volatility (variation in activity)
        volatility = hourly_data['std'].mean()
        if volatility > 20:
            volatility_desc = "High variability in activity levels throughout the day."
        elif volatility > 10:
            volatility_desc = "Moderate variability in activity levels."
        else:
            volatility_desc = "Consistent activity levels with minimal fluctuation."
        
        # Write analysis
        self.analysis_text.insert(tk.END, f"Pattern Type: {pattern_type}\n\n")
        self.analysis_text.insert(tk.END, f"{pattern_desc}\n\n")
        self.analysis_text.insert(tk.END, f"Peak Activity Hour: {int(peak_hour)}:00\n")
        self.analysis_text.insert(tk.END, f"Activity Distribution: Morning ({morning_activity:.1f}) | ")
        self.analysis_text.insert(tk.END, f"Midday ({midday_activity:.1f}) | Evening ({evening_activity:.1f})\n\n")
        self.analysis_text.insert(tk.END, f"Volatility: {volatility:.1f} - {volatility_desc}")
    
    def analyze_week_patterns(self):
        """Analyze patterns across the week"""
        # Calculate daily averages
        daily_avg = self.data.groupby('day_of_week')['activity_level'].mean()
        
        # Reindex to ensure correct order of days
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_avg = daily_avg.reindex(days_of_week)
        
        # Calculate weekday vs weekend difference
        weekday_avg = daily_avg[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']].mean()
        weekend_avg = daily_avg[['Saturday', 'Sunday']].mean()
        
        # Identify most and least active days
        most_active_day = daily_avg.idxmax()
        least_active_day = daily_avg.idxmin()
        
        # Determine weekly pattern type
        if weekend_avg > weekday_avg * 1.3:
            pattern_type = "Weekend Warrior"
            pattern_desc = "Significantly higher activity on weekends compared to weekdays."
        elif weekday_avg > weekend_avg * 1.3:
            pattern_type = "Workweek Active"
            pattern_desc = "Higher activity during the workweek with less active weekends."
        elif daily_avg.std() < 10:
            pattern_type = "Consistent Weekly Pattern"
            pattern_desc = "Relatively consistent activity levels throughout the week."
        else:
            pattern_type = "Variable Weekly Pattern"
            pattern_desc = "Activity levels vary significantly across different days of the week."
        
        # Write analysis
        self.analysis_text.insert(tk.END, f"Weekly Pattern Type: {pattern_type}\n\n")
        self.analysis_text.insert(tk.END, f"{pattern_desc}\n\n")
        self.analysis_text.insert(tk.END, f"Most Active Day: {most_active_day}\n")
        self.analysis_text.insert(tk.END, f"Least Active Day: {least_active_day}\n\n")
        self.analysis_text.insert(tk.END, f"Weekday Average: {weekday_avg:.1f}\n")
        self.analysis_text.insert(tk.END, f"Weekend Average: {weekend_avg:.1f}\n")
        
        # Add specific day analysis if needed
        self.analysis_text.insert(tk.END, "\nDaily Activity Levels:\n")
        for day in days_of_week:
            if day in daily_avg:
                self.analysis_text.insert(tk.END, f"{day}: {daily_avg[day]:.1f}\n")
    
    def toggle_simulation(self):
        """Toggle real-time simulation on/off"""
        if self.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        if self.simulation_active:
            # Stop simulation
            self.simulation_active = False
            self.sim_btn.config(text="Start Simulation")
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=1.0)
        else:
            # Start simulation
            self.simulation_active = True
            self.sim_btn.config(text="Stop Simulation")
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
    
    def run_simulation(self):
        """Run a real-time simulation updating the chart every few seconds"""
        if self.data is None:
            return
            
        # Switch to day view for simulation
        self.current_view = "day"
        
        days = sorted(self.data['timestamp'].dt.date.unique())
        if not days:
            return
            
        start_day = self.current_day
        
        # Loop through days
        while self.simulation_active:
            self.current_day = (self.current_day + 1) % len(days)
            
            # Update UI from main thread
            self.root.after(0, self.update_view_label)
            self.root.after(0, self.plot_kcandles)
            self.root.after(0, self.analyze_patterns)
            
            # Sleep for a few seconds before next update
            for _ in range(30):  # 3 seconds in 100ms increments
                if not self.simulation_active:
                    break
                time.sleep(0.1)
            
            # If we've gone through all days, stop the simulation
            if self.current_day == start_day:
                self.simulation_active = False
                self.root.after(0, lambda: self.sim_btn.config(text="Start Simulation"))
                break
    
    def export_view(self):
        """Export the current view as an image"""
        if self.data is None:
            messagebox.showinfo("No Data", "Please load data first")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Chart As"
        )
        
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Chart saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def show_pattern_guide(self):
        """Show the pattern guide window"""
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
        text.insert(tk.END, "KinetiCandles: Movement Pattern Reference Guide\n\n")
        text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Morning Peak Pattern
        text.insert(tk.END, "Morning Peak Pattern\n", "heading")
        text.insert(tk.END, "-" * 20 + "\n")
        text.insert(tk.END, "Visual Signature: Tall green candles in morning hours (6-9am) with progressively smaller candles afterward\n\n")
        text.insert(tk.END, "Interpretation: Morning-oriented person with highest energy early in day\n\n")
        text.insert(tk.END, "Health Implications: Often associated with good sleep hygiene and regular circadian rhythm\n\n")
        
        # Evening Peak Pattern
        text.insert(tk.END, "Evening Peak Pattern\n", "heading")
        text.insert(tk.END, "-" * 20 + "\n")
        text.insert(tk.END, "Visual Signature: Small morning candles with progressively larger candles in evening (5-8pm)\n\n")
        text.insert(tk.END, "Interpretation: Evening-oriented person with energy building throughout day\n\n")
        text.insert(tk.END, "Health Implications: May indicate delayed circadian rhythm or night owl chronotype\n\n")
        
        # Bimodal Pattern
        text.insert(tk.END, "Bimodal Pattern\n", "heading")
        text.insert(tk.END, "-" * 20 + "\n")
        text.insert(tk.END, "Visual Signature: Two distinct peaks (morning and evening) with a mid-day trough\n\n")
        text.insert(tk.END, "Interpretation: Work/commute influenced pattern or twice-daily exercise routine\n\n")
        text.insert(tk.END, "Health Implications: Often seen in people with structured work schedules and good work-life balance\n\n")
        
        # More patterns...
        text.insert(tk.END, "Weekend Warrior Pattern\n", "heading")
        text.insert(tk.END, "-" * 20 + "\n")
        text.insert(tk.END, "Visual Signature: Weekday vs. weekend patterns show opposite timing of peak activities\n\n")
        text.insert(tk.END, "Interpretation: Different routines between work and leisure days\n\n")
        text.insert(tk.END, "Health Implications: May indicate work-driven movement patterns rather than intrinsic preferences\n\n")
        
        # Format headings
        text.tag_configure("heading", font=("Arial", 12, "bold"))
        
        # Make text read-only
        text.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        KinetiCandles: Movement Pattern Analyzer
        Version 1.0
        
        A tool for visualizing and analyzing temporal movement patterns
        using K-plot (candlestick) visualization inspired by financial charts.
        
        This application helps researchers and individuals understand their
        movement behavior patterns throughout the day and week.
        
        Created for the LABDA Academy Hackathon.
        """
        
        messagebox.showinfo("About KinetiCandles", about_text)


# Function to generate sample data for testing
def generate_sample_data():
    """Generate sample accelerometer data for testing"""
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


def generate_high_res_sample_data():
    """Generate high-resolution sample accelerometer data for testing"""
    # Create a week of data with 10-second intervals for high-resolution analysis
    start_date = datetime.datetime(2023, 5, 1)
    days = 7
    interval_seconds = 10  # 10-second intervals
    
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
                    
                    # Base activity level from hourly pattern (similar to previous pattern)
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
                    # These patterns create variations within each hour that will be visible in high-res view
                    minute_factor = 1.0
                    
                    # Beginning of hour tends to be more active
                    if minute < 15:
                        minute_factor = 1.1
                    # Mid-hour dip
                    elif 25 <= minute < 40:
                        minute_factor = 0.9
                    # End of hour increase (e.g., preparing to transition)
                    elif minute >= 50:
                        minute_factor = 1.05
                    
                    # Add random noise at 10-second level
                    second_factor = np.random.normal(1, 0.05)
                    
                    # Calculate final activity
                    activity = base_activity * minute_factor * second_factor
                    
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
    if messagebox.askyesno("Sample Data", "Would you like to load high-resolution sample data for demonstration?"):
        app.data = generate_high_res_sample_data()
        app.update_view_label()
        app.plot_kcandles()
        app.analyze_patterns()
    
    root.mainloop()