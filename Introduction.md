# KinetiCandles: Movement Patterns for Healthier, Richer Living

## Project Overview

KinetiCandles bridges financial trading patterns and physical movement analysis, suggesting that understanding movement "investments" throughout the day leads to better "returns" in health and wellbeing. Just as traders use candlestick patterns to build wealth, people can use movement patterns to build health.

- **Kineti**: From "kinetic," relating to movement and physical activity
- **Candles**: Direct reference to candlestick charts (K-plots) from trading
- **Healthier, Richer**: Captures dual benefits of improved health through better movement patterns and wealth of insights from financial chart analysis

## Visualization Concept

KinetiCandles is a visualization tool for analyzing temporal movement patterns using K-plots (candlestick charts) similar to those used in financial trading. Like trading candlesticks that reveal market psychology, KinetiCandles reveal underlying patterns and drivers of human movement behavior.

### K-Plot Components for Movement Analysis:

- **Open**: Activity level at the **beginning** of a time period
- **High**: **Peak** activity level during the time period
- **Low**: **Minimum** activity level during the time period
- **Close**: Activity level at the **end** of the time period
- **K-line (moving average)**: Provides visualization of overall activity trend

### Pattern Interpretation:

- Long "bodies" indicate significant changes in activity within a time period
- Short "bodies" show consistent activity levels
- "Wicks" extending upward show brief periods of high activity
- Lower wicks show brief periods of low activity
- Long wicks indicate high variability within the time period

## Key Features

### Multi-Scale Visualization

- **Cross-Scale Visualizer**: Interactive tool allowing researchers to "zoom" between temporal scales (seconds to years)

- Multiple View Options

  :

  - Daily View: Hourly K-plots for a full day
  - Weekly View: Daily K-plots across a week
  - High-Resolution View: Minute-by-minute K-plots for selected time windows
  - Multi-Day View: 7 days side by side with hourly resolution, revealing weekly patterns

### Data Integration

- Integrates multi-device temporal data streams with different sampling rates
- Resolves synchronization issues common in multi-sensor movement studies
- Supports detection of abnormal values and imputation of missing data

### Analysis Methods

- **Time-domain analysis**
- **Frequency domain analysis**
- Complexity measures
  - Entropy measures to quantify movement regularity/complexity
  - Detrended fluctuation analysis to identify self-similarity across time scales
  - Poincaré plots to visualize correlation between consecutive movement intervals

## Movement Pattern Library

Just as trading has established patterns like "doji," "hammer," or "engulfing," KinetiCandles creates standardized movement pattern definitions. The pattern library includes:

### Basic Patterns

- **"Morning Peak"**: Activity primarily in morning hours
- **"Evening Active"**: Activity concentrated in evening hours
- **"Consistent Distributor"**: Activity evenly spread throughout day
- **"Biphasic Mover"**: Two distinct activity peaks during the day
- **"Weekend Shifter"**: Different patterns on weekends vs. weekdays
- **"Irregular Pattern"**: No consistent temporal structure

### Advanced Patterns

- **"Morning Spike"**: High activity in morning followed by decline
- **"Steady Climber"**: Gradually increasing activity throughout the day
- **"Active Dip"**: High activity with brief rest period
- **"Weekend Reversal"**: Pattern that inverts on weekends
- **Transition Patterns**: "Morning Surge," "Evening Cliff"
- **Anomaly Patterns**: "Activity Island"

## Implementation

### Tool Requirements

- CSV file with required columns:
  - timestamp: Date and time of measurement
  - activity_level: Numeric value representing activity intensity

### User Interface

- Navigation buttons to explore different days
- UI controls to select 1-4 hour windows for detailed analysis
- Default view focuses on 8-10am (typical morning activity period)
- Pattern guide accessible from Help menu
- Export capabilities for visualizations and analyses

### Simulation Mode

- Sample data generated at 1-second intervals for high-resolution analysis
- Includes minute-level patterns within each hour

## Value & Applications

- Detection of early signs of movement disorders or functional decline
- Identification of optimal movement patterns in sports performance
- Fatigue indicators in performance
- Pattern consistency as an indicator of habit strength
- Pattern evolution as a measure of behavior change

## Project Status

- First prototype ready for testing
- Basic visualization components implemented
- Pattern detection needs further development
- Ongoing implementation of:
  - Additional temporal pattern detection algorithms (wavelets, dynamic time warping)
  - User-friendly interface for interactive visualization
  - Statistical significance testing for identified patterns

## Methodology

The approach uses observation and machine learning techniques to identify representative patterns:

- Exploratory data analysis on movement datasets to identify naturally occurring patterns
- Clustering algorithms to find groups of similar temporal movement behaviors
- Visualizations showing how individual patterns relate to naturally occurring clusters
- Expert consultation and longitudinal validation

If establishing movement-specific patterns proves too complex, existing trading patterns can be adapted with movement-related interpretations.



# KinetiCandles: Movement Patterns for Healthier, Richer Living

## Project Overview

KinetiCandles is a comprehensive visualization and analysis tool that applies financial trading's candlestick chart (K-plot) methodology to human movement data. Just as traders use candlestick patterns to build wealth, individuals and researchers can use movement patterns to build health. This tool bridges the gap between financial analysis techniques and physical activity monitoring, offering a unique approach to understanding temporal movement behaviors.

## Core Features

### 1. Multi-Resolution Temporal Visualization

- **Daily View**: Hourly K-plots showing activity patterns across a full day
- **Weekly View**: Day-by-day K-plots displaying patterns across an entire week
- **High-Resolution View**: Minute-by-minute K-plots for detailed analysis of specific time windows

### 2. K-Plot Movement Visualization

- Candlestick Representation

  : Each time period displays four key metrics:

  - Open: Activity level at the beginning of the period
  - Close: Activity level at the end of the period
  - High: Maximum activity during the period
  - Low: Minimum activity during the period

- Visual Indicators

  :

  - Green candles: Activity increased during the time period
  - Red candles: Activity decreased during the time period
  - Long bodies: Significant changes in activity
  - Short bodies: Consistent activity levels
  - Long wicks: Brief periods of high/low activity

### 3. K-Line Trend Analysis

- Moving average visualization that smooths short-term fluctuations
- Reveals underlying activity trends throughout the day/week
- Helps identify major activity shifts and patterns

### 4. Pattern Recognition

- Automatic detection of common movement patterns:
  - Morning Peak: Highest activity in morning hours
  - Evening Peak: Activity builds throughout the day
  - Bimodal Pattern: Two distinct activity peaks with midday lull
  - Consistent Activity: Steady activity throughout the day
  - Weekend Warrior: Different patterns on weekdays vs. weekends
  - Activity Island: Isolated bursts within sedentary periods

### 5. Pattern Reference Library

- Built-in guide explaining how to interpret different movement patterns
- Standardized definitions similar to trading's "doji," "hammer," and "engulfing" patterns
- Health and lifestyle implications for each identified pattern

### 6. Advanced Analysis Tools

- Time-domain analysis: Variability metrics, consistency scores
- Frequency-domain analysis: Activity rhythm detection
- Non-linear analysis: Entropy measures, movement complexity

## Technical Features

### 1. Data Management

- Import CSV files with timestamp and activity level data
- Handles data from multiple accelerometer sources
- Automatic time synchronization for multi-device data

### 2. Interactive Controls

- Time window selection for high-resolution analysis
- Day-to-day navigation
- Simulation mode to automatically cycle through data

### 3. Export & Sharing

- Export visualizations as image files
- Save analysis reports

## Usage & Applications

### Research Applications

- Identify individual movement signatures and patterns
- Detect early signs of movement disorders or functional decline
- Track the impact of interventions on movement behaviors

### Clinical Applications

- Monitor recovery through changes in movement variability
- Assess adherence to physical activity recommendations
- Analyze circadian rhythm disruptions

### Sports & Fitness

- Identify optimal training patterns and recovery cycles
- Detect signs of overtraining or fatigue
- Optimize activity timing based on individual patterns

## Current Status

KinetiCandles is a functioning prototype with basic pattern detection and visualization capabilities. Ongoing development focuses on:

1. Refining the pattern detection algorithms
2. Expanding the pattern reference library
3. Adding more advanced statistical analysis tools
4. Enhancing visualization components for multi-scale pattern exploration

This innovative tool represents a significant advancement in temporal movement analysis, providing researchers and individuals with a powerful new framework for understanding human movement behavior through its inherent patterns.