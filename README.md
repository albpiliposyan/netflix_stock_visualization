# Netflix Stock - Exploratory Data Analysis

A simple EDA of Netflix (NFLX) stock prices from 2002 to 2026.

## Project Description

This notebook performs basic exploratory data analysis on Netflix stock data. It covers common EDA techniques like inspecting data, checking quality, visualizing trends, and analyzing distributions.

## Dataset

| Attribute | Value |
|-----------|-------|
| **Source** | Yahoo Finance |
| **Date Range** | May 2002 – January 2026 |
| **Records** | 5,961 trading days |
| **Features** | Open, High, Low, Close, Volume |

## Project Structure

```
netflix-stock-eda/
├── netflix_stock_eda.ipynb   # Jupyter Notebook
├── README.md                 
├── requirements.txt          
└── datasets/
    └── netflix_stock.csv     
```

## What's Covered

1. **Load Data** - Read CSV and inspect structure
2. **Data Quality** - Check missing values, duplicates
3. **Visualizations** - Price chart, volume chart
4. **Returns Analysis** - Histogram, basic stats
5. **Correlation** - Heatmap of features
6. **Box Plot** - Identify outliers
7. **Summary** - Key findings

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
jupyter notebook netflix_stock_eda.ipynb
```
