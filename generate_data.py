import pandas as pd
import numpy as np
import datetime
import os

def generate_1second_data(output_file="kineticandles_data.csv", days=1, start_day=0, time_range=None):
    """Generate high-resolution accelerometer data with 1-second intervals.
    
    Args:
        output_file: Path to save the CSV file
        days: Number of days to generate (default: 1)
        start_day: Starting day offset (0=Monday, 1=Tuesday, etc.)
        time_range: Optional tuple of (start_hour, end_hour) to limit data to specific hours
                   If None, generates full days
    """
    print(f"Generating 1-second resolution data for {days} days...")
    
    # Create data with 1-second intervals
    start_date = datetime.datetime(2023, 5, 1 + start_day)  # May 1, 2023 was a Monday
    interval_seconds = 1
    
    # Create empty dataframe
    data = []
    
    # Process time range
    if time_range:
        start_hour, end_hour = time_range
        hours_per_day = end_hour - start_hour
    else:
        start_hour, end_hour = 0, 24
        hours_per_day = 24
    
    # Calculate estimated data points for progress reporting
    total_points = days * hours_per_day * 60 * 60
    points_generated = 0
    
    # Generate data points for each day
    for day in range(days):
        current_date = start_date + datetime.timedelta(days=day)
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5
        
        # Report progress
        print(f"Generating data for {current_date.strftime('%A, %Y-%m-%d')}...")
        
        # Generate data points for the specified hours
        for hour in range(start_hour, end_hour):
            for minute in range(60):
                for second in range(60):
                    timestamp = current_date + datetime.timedelta(hours=hour, minutes=minute, seconds=second)
                    
                    # Base activity level from hourly pattern
                    if not is_weekend:  # Weekday pattern
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
                    
                    # Add second-level patterns for 1-second data
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
                    
                    # Update progress counter
                    points_generated += 1
            
            # Print progress every hour
            progress = points_generated / total_points * 100
            print(f"Progress: {progress:.1f}% ({points_generated}/{total_points} points)")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add day_of_week column
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    # Save to CSV
    print(f"Saving data to {output_file}...")
    df.to_csv(output_file, index=False)
    
    # Print file information
    file_size_kb = os.path.getsize(output_file) / 1024
    file_size_mb = file_size_kb / 1024
    print(f"File saved: {output_file}")
    
    if file_size_mb >= 1:
        print(f"File size: {file_size_mb:.2f} MB")
    else:
        print(f"File size: {file_size_kb:.2f} KB")
        
    print(f"Number of rows: {len(df)}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Ready to use with KinetiCandles!")

# Example use cases

def create_single_day_data():
    """Generate 1-second data for a full Monday (24 hours)."""
    generate_1second_data(
        output_file="kineticandles_fullday.csv",
        days=1,
        start_day=0  # Monday
    )

def create_morning_hours_data():
    """Generate 1-second data for morning hours (6:00-10:00 AM) for Monday."""
    generate_1second_data(
        output_file="kineticandles_morning.csv",
        days=1,
        start_day=0,  # Monday
        time_range=(6, 10)  # 6:00 AM to 10:00 AM
    )

def create_workweek_data():
    """Generate 1-second data for a work week (Monday-Friday)."""
    generate_1second_data(
        output_file="kineticandles_workweek.csv",
        days=5,
        start_day=0  # Start on Monday
    )

def create_weekend_data():
    """Generate 1-second data for a weekend (Saturday and Sunday)."""
    generate_1second_data(
        output_file="kineticandles_weekend.csv",
        days=2,
        start_day=5  # Start on Saturday
    )

if __name__ == "__main__":
    # Uncomment the option you want to use:
    
    # Option 1: Generate data for a 4-hour morning period (smaller file, ~57MB for 4 hours)
    generate_1second_data(
        output_file="kineticandles_data.csv",
        days=1,
        time_range=(6, 10)  # 6:00 AM to 10:00 AM
    )
    
    # Option 2: Generate data for a full day (larger file, ~340MB for 24 hours)
    # create_single_day_data()
    
    # Option 3: Generate data for a 5-day work week (very large file, ~1.7GB)
    # create_workweek_data()
    
    # Option 4: Generate data for a weekend (large file, ~680MB)
    # create_weekend_data()