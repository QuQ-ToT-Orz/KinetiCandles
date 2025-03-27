# Hackathon

### 0 Title
KinetiCandles: Movement Patterns for Healthier, Richer Living

This name creates a perfect connection between your K-plot inspiration and the health/wealth benefits of understanding movement patterns:

- Kineti - From "kinetic," relating to movement and physical activity
- Candles - Direct reference to candlestick charts (K-plots) from trading
- Healthier, Richer - Captures the dual benefits: improved health through better movement patterns and the wealth of insights drawn from financial chart analysis techniques

The name "KinetiCandles" cleverly bridges the gap between financial trading patterns and physical movement patterns, suggesting that understanding your movement "investments" throughout the day can lead to better "returns" in health and wellbeing. Just as traders use candlestick patterns to build wealth, people can use movement patterns to build health.

### 1 Candlestick Charts from Trading
A visualization tool for analyzing temporal movement patterns using K-plots (candlestick charts) similar to those used in financial trading. The app allows you to upload your own accelerometer data and visualize it in daily or weekly views.

Like trading candlesticks that reveal market psychology, KinetiCandles reveal the underlying patterns and drivers of human movement behavior.

KinetiCandles creates movement K-plots that show activity patterns with K-lines (moving averages) to provide a clearer visualization of the overall activity trend throughout the day. This helps researchers see the underlying trend by smoothing out short-term fluctuations.

As traders learn to "read" candlestick charts, researchers and practitioners can learn to "read" movement patterns:

- Open: Activity level at the **beginning** of a time period
- High: **Peak** activity level during the time period
- Low: **Minimum** activity level during the time period
- Close: Activity level at the **end** of the time period

Long "bodies" would indicate significant changes in activity within the time period, while short "bodies" would show consistent activity levels. "Wicks (Lines)" extending upward would show brief periods of high activity, while lower wicks show brief periods of low activity. Long wicks indicate high variability within the time period.

Open and close values in candlestick plots are sensitive to small time offsets, while the highs and lows remain unaffected. This means that even with the same price movement during a time frame containing exactly the same information, the pattern could look different due to time offset. There are several ways to show price movement that aren't affected by time at all. One is tick charts, which generate a new candle every time a certain number of trades occur. Another is range bars, which create candles that are all the same size as price moves through the levels. Finally, there are volume/dollar bars, which create a new candle whenever a certain volume/dollar amount is traded.

Researchers can upload accelerometer data and receive comprehensive movement variability metrics, visualizations, and interpretation guides. By using this tool similar to candle charts, users can work toward getting healthier and richer insights into movement patterns.

### 2 Visualization Interpretation

KinetiCandles integrates multi-device temporal data streams with different sampling rates and timestamps into a unified timeline, resolving synchronization issues that commonly plague multi-sensor movement behavior studies.

Candlestick charts in trading typically have much higher resolution, detecting cyclical patterns across multiple time scales simultaneously (hourly, daily, weekly, seasonal). The Cross-Scale Visualizer is an interactive visualization tool that allows researchers to "zoom" between different temporal scales (seconds to years) in movement data. The tool supports hourly, minute-level, and Multi-Day View: display 7 days side by side with hourly resolution, which reveals weekly patterns and day-to-day variations.

It reveals recurrent temporal patterns and cyclical behaviors in longitudinal movement data through visual analytics and machine learning techniques, allowing researchers to discover hidden rhythms and behavioral signatures within seemingly complex data.

KinetiCandles simplifies the detection of abnormal values and imputation of missing data through real-time data collection, temporal pattern recognition, and visualization of continuous activity monitoring with focus on temporal patterns.

### 3 Pattern Books or Movement Pattern Library Reference
There are existing libraries for patterns in trading and also many existing tools (e.g., webpage [Candle Speed and Acceleration — Indicator by readysetfire — TradingView](https://www.tradingview.com/script/7MtlSnCj-Candle-Speed-and-Acceleration/), commercial tools [Automated Candle Pattern Recognition - TrendSpider](https://help.trendspider.com/kb/automated-technical-analysis/candlestick-pattern-recognition), etc.) to identify these patterns. Just as trading has established patterns like "doji," "hammer," or "engulfing," KinetiCandles creates standardized movement pattern definitions. Patterns like "doji" (open ≈ close) would indicate periods without trend in activity.

Physical cards showing common movement pattern templates provide visual representations of different activity rhythms, useful for researchers to quickly identify pattern types including:

- Basic Patterns
- Transition Patterns (Morning Surge, Evening Cliff)
- Anomaly Patterns (Activity Island)
- Weekly Pattern Variations (Weekend Reversal)
- Pattern Consistency (Habit Strength)
- Pattern Evolution (Behavior Change)

A printed reference guide explains how to interpret temporal patterns, including case studies, example interpretations, and explanations of different temporal movement patterns and their potential implications.

Users can annotate data with predefined templates of common movement patterns:

- "Morning Peak" - Activity primarily in morning hours
- "Evening Active" - Activity concentrated in evening hours
- "Consistent Distributor" - Activity evenly spread throughout day
- "Biphasic Mover" - Two distinct activity peaks during the day
- "Weekend Shifter" - Distinctly different patterns on weekends vs. weekdays
- "Irregular Pattern" - No consistent temporal structure

As traders identify patterns like "engulfing" or "hammer," users can define common movement patterns:

- "Morning Spike": High activity in morning followed by decline
- "Steady Climber": Gradually increasing activity throughout the day
- "Active Dip": High activity with brief rest period
- "Weekend Reversal": Pattern that inverts on weekends

The tool includes an open repository of validated movement pattern templates that researchers could use to quickly identify known patterns in their data. The library would grow as users contribute new validated patterns with metadata about context and population.

Simple matching algorithms identify which pattern a person follows, presented as simple infographic cards rather than complex analytics.

Value includes detecting early signs of movement disorders or functional decline, identifying optimal movement patterns and fatigue indicators in sports performance.

### 4 Other Simple Metrics That Capture Meaningful Differences Between Patterns
KinetiCandles adds three sub-options under features:

- Time-domain analysis
- Frequency domain analysis
- Complexity measures of movement patterns include:
  - Entropy measures to quantify movement regularity/complexity
  - Detrended fluctuation analysis to identify self-similarity across time scales
  - Poincaré plots to visualize the correlation between consecutive movement intervals

### 5 Tool Description

Launch the application to access the graphical user interface. Choose to load sample data or import your own CSV file with at least the following columns:

- timestamp: Date and time of the measurement
- activity_level: Numeric value representing activity intensity

Use the controls to switch between three visualization views:

- Daily View: Shows hourly K-plots for a full day
- Weekly View: Shows daily K-plots across a week
- High-Resolution View: Shows minute-by-minute K-plots for a selected time window

Use the navigation buttons to explore different days with Previous/Next buttons. UI controls allow selection of a 1-4 hour window for detailed analysis, zooming into specific parts of the day (morning routine, workout sessions, etc.). Default view focuses on 8-10am (typical morning activity period). For high-resolution analysis, select a time window and click "Apply."

Access the built-in pattern guide from the Help menu to learn about different movement patterns and their interpretations. Export visualizations or pattern analyses as needed.

The simulation mode includes sample data generated at 1-second intervals for realistic high-resolution analysis, including minute-level patterns within each hour.

### Value

The contribution would be creating these standardized references to temporal movement pattern classification and interpretation, which future researchers could build upon and validate empirically. Just as traders use high-resolution K-plots to identify precise entry and exit points, researchers could use high-resolution movement K-plots to pinpoint optimal times for interventions or to identify subtle changes in movement behaviors that might indicate health changes.

Each pattern has a memorable name, clear visual and quantitative characteristics, context for interpretation, and health implications.


### Status
First prototype ready for testing - basic visualization components implemented but pattern detection needs work. Implementation of additional temporal pattern detection algorithms (wavelets, dynamic time warping), refinement of a user-friendly interface for interactive visualization components to explore patterns at multiple time scales, and integration of statistical significance testing for identified patterns is ongoing.

The approach uses observation and even machine learning techniques to identify representative patterns. We use exploratory data analysis on movement datasets to identify naturally occurring patterns, apply clustering algorithms to find groups of similar temporal movement behaviors, and create visualizations that show how individual patterns relate to these naturally occurring clusters.

In trading, the interpretations for candlestick patterns like "doji," "hammer," and "engulfing" were developed through a combination of historical observation, empirical testing, theoretical market psychology, and refinement through practice. KinetiCandles uses a Big Data-Driven Approach (machine learning techniques, clustering) and Expert Consultation and Longitudinal Validation. If establishing patterns specifically identified for human movement becomes too complicated and time-consuming, we can adapt existing patterns from trading and provide interpretations related to human movement.