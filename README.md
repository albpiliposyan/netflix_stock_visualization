# Netflix Stock Visualization Dashboard

A simple Dash dashboard and notebook project for Netflix (NFLX) stock prices from 2002 to 2026.

## Project Description

This project contains:

- `netflix_stock_eda.ipynb` - exploratory data analysis
- `netflix_stock_story.ipynb` - story, insights, and Plotly charts
- `app.py` - a three-page Dash dashboard draft based on the story notebook

## Dataset

| Attribute | Value |
|-----------|-------|
| **Source** | Yahoo Finance |
| **Date Range** | May 2002 – January 2026 |
| **Records** | 5,961 trading days |
| **Features** | Open, High, Low, Close, Volume |

## Project Structure

```
netflix_stock_visualization/
├── app.py
├── assets/
│   └── styles.css
├── DASHBOARD_GUIDE.md
├── netflix_stock_eda.ipynb
├── netflix_stock_story.ipynb
├── README.md
├── requirements.txt
└── datasets/
    └── netflix_stock.csv
```

## Dashboard Pages

1. **History** - full price history, story eras, moving averages, and summary cards
2. **Performance** - annual return winners/losers and monthly seasonality heatmap
3. **Risk & Seasonality** - crash-window candlesticks, volume, return distribution, and rolling volatility

The dashboard includes Dash callbacks for year ranges, dropdowns, sliders, moving-average toggles, and buttons.

For detailed chart explanations and implementation notes, see [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md).

## Requirements

```bash
pip install -r requirements.txt
```

## Run the Dashboard

From this folder:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:8050
```

If port `8050` is already used, run it on another port:

```bash
python app.py --port 8051
```

Then open:

```text
http://127.0.0.1:8051
```

For development with Dash debug mode:

```bash
python app.py --debug
```

You can combine both options:

```bash
python app.py --port 8051 --debug
```

## Deploy on Render

This dashboard is ready to run as a Render **Web Service**.

Use these settings in the Render dashboard:

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:server` |

The `.python-version` file pins the deployment to Python 3.14 without requiring a Render environment variable.

Why `app:server`? The Dash app in `app.py` exposes the Flask server as:

```python
server = app.server
```

Render will run that server with Gunicorn in production.

## Run the Notebooks

```bash
jupyter notebook netflix_stock_eda.ipynb
```
