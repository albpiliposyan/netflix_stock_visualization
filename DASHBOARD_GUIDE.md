# Dashboard Guide and Chart Explanations

This guide explains what each dashboard chart shows and how the main parts are implemented.

## Dashboard Story

The dashboard tells a simple story: Netflix stock had a long growth period, a major decline around 2021-2022, and then a recovery period. Each page focuses on one part of that story.

## Page 1: History

This page gives the high-level view of the whole Netflix stock journey.

### Summary Cards

The four cards at the top show:

- **Latest close** - the most recent closing price in the dataset.
- **All-time high** - the highest closing price reached by Netflix.
- **Total return** - the percentage growth from the first date in the dataset to the last date.
- **30-day volatility** - recent short-term risk, calculated as the 30-day rolling standard deviation of daily returns.

Implementation details:

- These cards are created by the `summary_cards()` function.
- The card design is reused through the helper function `metric_card()`.
- The values are calculated directly from the cleaned dataframe `df`.

### Long-Term Price History

This chart shows the Netflix closing price over time. It is the main story chart of the dashboard.

What it shows:

- The red line is the daily Netflix closing price.
- Optional moving average lines show smoother long-term trends.
- Shaded background regions mark important story periods:
  - DVD era
  - streaming rise
  - COVID period
  - 2022 crash
  - recovery period

Interactive controls:

- **Year range slider** changes the visible time period.
- **50-day moving average** toggle adds or removes the short-term trend line.
- **200-day moving average** toggle adds or removes the long-term trend line.
- **Reset range** returns the chart to the full dataset period.

Implementation details:

- The chart is created in the `update_history_chart()` callback.
- The main price line is a Plotly `go.Scatter` trace.
- Moving averages are calculated in `load_data()` using:

```python
data["MA_50"] = data["Close"].rolling(50).mean()
data["MA_200"] = data["Close"].rolling(200).mean()
```

- Story periods are added with Plotly vertical rectangles using `fig.add_vrect()`.
- When the year range changes, the x-axis and y-axis are recalculated so the selected period is shown clearly.

## Page 2: Performance

This page compares Netflix stock performance by year and month.

### Year by Year: Winners and Losers

This bar chart shows annual stock return for each selected year.

What it shows:

- Each bar represents one year.
- Green bars mean Netflix ended the year higher than it started.
- Red bars mean Netflix ended the year lower than it started.
- The zero line separates positive and negative annual performance.

Interactive controls:

- **Year range slider** filters which years are shown.
- **Show labels** dropdown controls whether percentage labels appear above the bars.

Implementation details:

- Annual returns are calculated in the `annual_returns()` function.
- The formula is:

```python
Return_Pct = (last_close / first_close - 1) * 100
```

- The chart is updated by the `update_performance()` callback.
- The chart uses Plotly `go.Bar`.
- Colors are assigned conditionally: green for positive returns and red for negative returns.

### Monthly Return Heatmap

This heatmap shows how Netflix performed month by month across years.

What it shows:

- Each row is a year.
- Each column is a month.
- Each cell shows the cumulative daily return for that month.
- Green cells show positive monthly return.
- Red cells show negative monthly return.
- Stronger color means a larger positive or negative move.

Why it is useful:

- It helps identify whether some months were usually stronger or weaker.
- It also makes unusual months visible quickly, especially during crash or recovery periods.

Implementation details:

- The chart is also updated by the `update_performance()` callback.
- The dataframe is reshaped with a pivot table:

```python
pivot = selected_df.pivot_table(
    values="Daily_Return",
    index="Year",
    columns="Month",
    aggfunc="sum"
)
```

- The heatmap is created with Plotly Express `px.imshow()`.
- The color scale is `RdYlGn`, centered at zero, so positive and negative months are visually separated.
- The chart height is adjusted based on the number of years selected, so rows remain readable.

## Page 3: Risk & Seasonality

This page focuses on risk, volatility, and price behavior during selected periods.

### Price and Volume

This chart combines weekly price candles and trading volume.

What it shows:

- The upper chart shows weekly candlesticks.
- Each candlestick summarizes one week:
  - open price
  - high price
  - low price
  - close price
- Green candles mean the week closed higher than it opened.
- Red candles mean the week closed lower than it opened.
- The lower chart shows weekly trading volume in millions.
- Peak and trough annotations mark the highest and lowest close inside the selected period.

Interactive controls:

- **Focus period** dropdown changes the period being analyzed:
  - full history
  - streaming era
  - 2022 crash window
  - recovery

Implementation details:

- The chart is created in the `update_risk()` callback.
- Daily data is converted to weekly data using `resample("W")`.
- The upper chart uses Plotly `go.Candlestick`.
- The lower chart uses Plotly `go.Bar` for volume.
- The two plots are placed together with `make_subplots()`.

### Risk Profile

This section contains two charts: daily return distribution and rolling volatility.

#### Daily Return Distribution

This histogram shows how daily returns are distributed during the selected period.

What it shows:

- Most days are usually close to 0% return.
- Wider spread means more unstable daily movement.
- Very negative or very positive bars show extreme trading days.

Interactive control:

- **Histogram bins** changes how many bars are used in the histogram.
- More bins show more detail.
- Fewer bins give a smoother summary.

Implementation details:

- The histogram uses the `Daily_Return` column.
- It is created with Plotly `go.Histogram`.
- The selected bin count is passed into the callback through the `return-bins` slider.

#### Rolling Volatility

This line chart shows how risky the stock was over time.

What it shows:

- The y-axis is the rolling standard deviation of daily returns.
- Higher values mean stronger price swings.
- Lower values mean calmer trading behavior.

Interactive control:

- **Volatility window** changes the rolling window size.
- A shorter window reacts faster to sudden changes.
- A longer window creates a smoother volatility trend.

Implementation details:

- Rolling volatility is calculated inside `update_risk()` based on the selected window:

```python
focus[f"Volatility_{vol_window}"] = focus["Daily_Return"].rolling(vol_window).std()
```

- The chart uses Plotly `go.Scatter`.
- The area under the line is filled to make high-volatility periods easier to see.

## General Implementation Details

The dashboard is implemented in `app.py` using Dash.

Important parts:

- `load_data()` reads `datasets/netflix_stock.csv`, parses the date index, sorts the data, and creates derived columns.
- `app.layout` defines the shared structure: URL location, header, navigation, page container, and footer.
- `render_page()` switches between the three dashboard pages based on the URL path.
- `chart_card()` and `metric_card()` keep the visual structure consistent across pages.
- `assets/styles.css` contains the dashboard styling, card layout, navigation highlight, controls, and responsive behavior.

Main calculated columns:

| Column | Meaning |
|--------|---------|
| `Daily_Return` | Daily percentage price change |
| `MA_50` | 50-day moving average of closing price |
| `MA_200` | 200-day moving average of closing price |
| `Volatility_30` | 30-day rolling standard deviation of daily returns |
| `Year` | Year extracted from the date |
| `Month` | Month extracted from the date |

Main callbacks:

| Callback | Purpose |
|----------|---------|
| `render_page()` | Displays the correct page and highlights the active navigation link |
| `reset_history_range()` | Resets the history page year slider |
| `update_history_chart()` | Updates the price history chart and moving averages |
| `update_performance()` | Updates annual returns, monthly heatmap, and performance cards |
| `update_risk()` | Updates risk cards, price/volume chart, histogram, and volatility chart |

Plotly chart interactions:

- Hover over points, bars, cells, and candles to see exact values.
- Drag across a time-based chart to zoom in.
- Double-click the chart or use the toolbar reset button to zoom out.
- Some charts have toolbar buttons for pan, zoom, and image export.
