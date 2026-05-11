import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from plotly.subplots import make_subplots


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datasets" / "netflix_stock.csv"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PLOT_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "responsive": True,
}

NAV_LINKS = [
    ("History", "/"),
    ("Performance", "/performance"),
    ("Risk & Seasonality", "/risk"),
]

ERAS = [
    ("2002-05-23", "2010-12-31", "rgba(100,100,100,0.08)", "DVD Era", 0),
    ("2011-01-01", "2019-12-31", "rgba(78,170,100,0.08)", "Streaming Rise", 0),
    ("2020-01-01", "2021-11-17", "rgba(255,200,0,0.12)", "COVID", 0),
    ("2021-11-17", "2022-12-31", "rgba(229,9,20,0.10)", "2022 Crash", -18),
    ("2023-01-01", "2026-12-31", "rgba(78,170,100,0.10)", "Recovery", -36),
]

PERIODS = {
    "all": ("Full history", None, None),
    "streaming": ("Streaming era", "2010-01-01", None),
    "crash": ("2022 crash window", "2021-01-01", "2023-12-31"),
    "recovery": ("Recovery", "2023-01-01", None),
}


def year_marks(min_year, max_year, step=3):
    marks = {year: str(year) for year in range(min_year, max_year + 1, step)}
    marks[min_year] = str(min_year)
    marks[max_year] = str(max_year)
    return marks


def load_data():
    data = pd.read_csv(DATA_PATH, header=[0, 1], index_col=0)
    data.columns = data.columns.get_level_values(0)
    data.index = pd.to_datetime(data.index)
    data.index.name = "Date"
    data = data.sort_index()

    data["Daily_Return"] = data["Close"].pct_change() * 100
    data["MA_50"] = data["Close"].rolling(50).mean()
    data["MA_200"] = data["Close"].rolling(200).mean()
    data["Volatility_30"] = data["Daily_Return"].rolling(30).std()
    data["Year"] = data.index.year
    data["Month"] = data.index.month
    return data


df = load_data()


def annual_returns():
    yearly = df.groupby("Year")["Close"].agg(first="first", last="last")
    yearly["Return_Pct"] = (yearly["last"] / yearly["first"] - 1) * 100
    return yearly[yearly.index >= 2003]


yearly_df = annual_returns()
MIN_YEAR = int(df["Year"].min())
MAX_YEAR = int(df["Year"].max())


def money(value):
    return f"${value:,.2f}"


def pct(value):
    return f"{value:+.1f}%"


def normalize_year_range(year_range, min_year=MIN_YEAR, max_year=MAX_YEAR):
    if not year_range or len(year_range) != 2:
        return min_year, max_year
    start_year, end_year = sorted([int(year_range[0]), int(year_range[1])])
    return max(start_year, min_year), min(end_year, max_year)


def year_bounds(year_range):
    start_year, end_year = normalize_year_range(year_range)
    start = max(pd.Timestamp(f"{start_year}-01-01"), df.index.min())
    end = min(pd.Timestamp(f"{end_year}-12-31"), df.index.max())
    return start, end


def metric_card(title, value, note=None):
    return html.Div(
        className="metric-card",
        children=[
            html.P(title, className="metric-title"),
            html.H3(value),
            html.P(note or "", className="metric-note"),
        ],
    )


def chart_card(title, children, subtitle=None):
    return html.Section(
        className="card",
        children=[
            html.Div(
                className="card-heading",
                children=[
                    html.H2(title),
                    html.P(subtitle) if subtitle else None,
                ],
            ),
            children,
        ],
    )


def nav_links(pathname):
    pathname = pathname or "/"
    children = []
    for label, href in NAV_LINKS:
        is_active = pathname == href or (href == "/" and pathname == "/history")
        class_name = "nav-link is-active" if is_active else "nav-link"
        children.append(dcc.Link(label, href=href, className=class_name))
    return children


def graph_tip():
    return html.P(
        "Tip: drag across the chart to zoom; double-click the plot or use the toolbar reset button to zoom out.",
        className="graph-tip",
    )


def app_header():
    return html.Header(
        className="app-header",
        children=[
            html.Div(
                children=[
                    html.P("NFLX Dashboard", className="brand-label"),
                    html.H1("Netflix Stock Story"),
                    html.P(
                        "A pre-deployment Dash dashboard built from the EDA and story notebook insights.",
                        className="header-subtitle",
                    ),
                ]
            ),
            html.Nav(
                id="page-nav",
                className="page-nav",
                children=nav_links("/"),
            ),
        ],
    )


def summary_cards():
    latest = df.iloc[-1]
    peak_date = df["Close"].idxmax()
    total_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
    return html.Div(
        className="metric-grid",
        children=[
            metric_card("Latest close", money(latest["Close"]), f"Last trading day: {df.index[-1].date()}"),
            metric_card("All-time high", money(df["Close"].max()), f"Reached on {peak_date.date()}"),
            metric_card("Total return", f"{total_return:,.0f}%", f"Since {df.index[0].date()}"),
            metric_card("30-day volatility", f"{latest['Volatility_30']:.2f}%", "Daily return standard deviation"),
        ],
    )


def history_layout():
    return html.Div(
        className="page-content",
        children=[
            summary_cards(),
            chart_card(
                "Long-Term Price History",
                html.Div(
                    children=[
                        html.Div(
                            className="controls-row history-controls",
                            children=[
                                html.Div(
                                    className="control wide-control",
                                    children=[
                                        html.Label("Year range"),
                                        dcc.RangeSlider(
                                            id="history-year-range",
                                            min=MIN_YEAR,
                                            max=MAX_YEAR,
                                            value=[MIN_YEAR, MAX_YEAR],
                                            marks=year_marks(MIN_YEAR, MAX_YEAR),
                                            step=1,
                                            tooltip={"placement": "bottom", "always_visible": False},
                                        ),
                                        html.P(id="history-range-summary", className="control-note"),
                                    ],
                                ),
                                html.Div(
                                    className="control compact-control ma-control",
                                    children=[
                                        html.Label("Moving averages"),
                                        dcc.Checklist(
                                            id="ma-selector",
                                            options=[
                                                {"label": "50-day", "value": "MA_50"},
                                                {"label": "200-day", "value": "MA_200"},
                                            ],
                                            value=["MA_50", "MA_200"],
                                            className="toggle-list",
                                        ),
                                    ],
                                ),
                                html.Button("Reset range", id="history-reset", className="secondary-button", n_clicks=0),
                            ],
                        ),
                        graph_tip(),
                        dcc.Graph(id="history-chart", config=PLOT_CONFIG),
                    ]
                ),
                "The same long-climb chart from the story notebook, with simple controls for dates and trend lines.",
            ),
        ],
    )


def performance_layout():
    return html.Div(
        className="page-content",
        children=[
            html.Div(id="performance-cards", className="metric-grid"),
            chart_card(
                "Year by Year: Winners and Losers",
                html.Div(
                    children=[
                        html.Div(
                            className="controls-row",
                            children=[
                                html.Div(
                                    className="control wide-control",
                                    children=[
                                        html.Label("Year range"),
                                        dcc.RangeSlider(
                                            id="year-range",
                                            min=int(yearly_df.index.min()),
                                            max=int(yearly_df.index.max()),
                                            value=[int(yearly_df.index.min()), int(yearly_df.index.max())],
                                            marks=year_marks(int(yearly_df.index.min()), int(yearly_df.index.max())),
                                            step=1,
                                            tooltip={"placement": "bottom", "always_visible": False},
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="control",
                                    children=[
                                        html.Label("Show labels"),
                                        dcc.Dropdown(
                                            id="label-toggle",
                                            options=[
                                                {"label": "Show return labels", "value": "show"},
                                                {"label": "Hide return labels", "value": "hide"},
                                            ],
                                            value="show",
                                            clearable=False,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Graph(id="annual-return-chart", config=PLOT_CONFIG),
                    ]
                ),
                "Annual return makes the main story visible: rapid growth, a severe 2022, and the recovery after it.",
            ),
            chart_card(
                "Monthly Return Heatmap",
                dcc.Graph(id="monthly-heatmap", config=PLOT_CONFIG),
                "A compact seasonality view from the story notebook, filtered by the selected years.",
            ),
        ],
    )


def risk_layout():
    return html.Div(
        className="page-content",
        children=[
            html.Div(id="risk-cards", className="metric-grid"),
            html.Div(
                className="controls-row",
                children=[
                    html.Div(
                        className="control",
                        children=[
                            html.Label("Focus period"),
                            dcc.Dropdown(
                                id="period-selector",
                                options=[{"label": label, "value": key} for key, (label, _, _) in PERIODS.items()],
                                value="crash",
                                clearable=False,
                            ),
                        ],
                    ),
                ],
            ),
            chart_card(
                "Price and Volume",
                html.Div(
                    children=[
                        graph_tip(),
                        dcc.Graph(id="crash-chart", config=PLOT_CONFIG),
                    ]
                ),
                "Weekly candles and volume make each selected period easier to read than daily noise.",
            ),
            chart_card(
                "Risk Profile",
                html.Div(
                    children=[
                        html.Div(
                            className="controls-row risk-profile-controls",
                            children=[
                                html.Div(
                                    className="control",
                                    children=[
                                        html.Label("Histogram bins"),
                                        dcc.Slider(
                                            id="return-bins",
                                            min=20,
                                            max=120,
                                            step=10,
                                            value=80,
                                            marks={20: "20", 50: "50", 80: "80", 120: "120"},
                                            tooltip={"placement": "bottom", "always_visible": False},
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="control",
                                    children=[
                                        html.Label("Volatility window"),
                                        dcc.Slider(
                                            id="vol-window",
                                            min=10,
                                            max=90,
                                            step=5,
                                            value=30,
                                            marks={10: "10d", 30: "30d", 60: "60d", 90: "90d"},
                                            tooltip={"placement": "bottom", "always_visible": False},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Graph(id="risk-chart", config=PLOT_CONFIG),
                    ]
                ),
                "Return distribution and rolling volatility show how risky Netflix felt in each period.",
            ),
        ],
    )


def not_found_layout():
    return html.Div(
        className="page-content",
        children=[
            html.Div(
                className="card empty-state",
                children=[
                    html.H2("Page not found"),
                    html.P("Use the navigation above to open a dashboard page."),
                    dcc.Link("Go to History", href="/", className="primary-link"),
                ],
            )
        ],
    )


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Netflix Stock Dashboard"
server = app.server

app.layout = html.Div(
    children=[
        dcc.Location(id="url"),
        app_header(),
        html.Main(id="page-container"),
        html.Footer(
            className="app-footer",
            children="Dataset: Yahoo Finance NFLX daily stock prices, May 2002 to January 2026.",
        ),
    ]
)


@app.callback(
    Output("page-container", "children"),
    Output("page-nav", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    if pathname in (None, "/", "/history"):
        return history_layout(), nav_links(pathname)
    if pathname == "/performance":
        return performance_layout(), nav_links(pathname)
    if pathname == "/risk":
        return risk_layout(), nav_links(pathname)
    return not_found_layout(), nav_links(pathname)


@app.callback(
    Output("history-year-range", "value"),
    Input("history-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_history_range(_):
    return [MIN_YEAR, MAX_YEAR]


@app.callback(
    Output("history-chart", "figure"),
    Output("history-range-summary", "children"),
    Input("history-year-range", "value"),
    Input("ma-selector", "value"),
)
def update_history_chart(year_range, selected_mas):
    selected_mas = [column for column in (selected_mas or []) if column in {"MA_50", "MA_200"}]
    start, end = year_bounds(year_range)
    visible = df.loc[(df.index >= start) & (df.index <= end)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            name="Close Price",
            showlegend=True,
            line={"color": "#E50914", "width": 1.8},
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:.2f}<extra></extra>",
        )
    )

    ma_styles = {
        "MA_50": ("50-day MA", "#F5A623"),
        "MA_200": ("200-day MA", "#4A90E2"),
    }
    for column in selected_mas:
        label, color = ma_styles[column]
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[column],
                name=label,
                line={"color": color, "width": 1.3, "dash": "dot"},
                hovertemplate=f"{label}: $%{{y:.2f}}<extra></extra>",
            )
        )

    for x0, x1, color, label, yshift in ERAS:
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=color,
            line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation={"font_size": 11, "font_color": "#404040", "yshift": yshift},
        )

    y_columns = ["Close"] + selected_mas
    y_values = visible[y_columns].stack().dropna()
    y_min, y_max = float(y_values.min()), float(y_values.max())
    padding = max((y_max - y_min) * 0.08, 1)

    fig.update_layout(
        title=f"Netflix Stock Price - {start.year} to {end.year}",
        template="plotly_white",
        height=520,
        hovermode="x unified",
        showlegend=True,
        margin={"l": 40, "r": 24, "t": 70, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        xaxis={"title": "Date", "range": [start, end], "rangeslider": {"visible": False}},
        yaxis={"title": "Price (USD)", "range": [y_min - padding, y_max + padding]},
    )
    summary = f"Showing {start.date()} to {end.date()} with {len(visible):,} trading days."
    return fig, summary


@app.callback(
    Output("performance-cards", "children"),
    Output("annual-return-chart", "figure"),
    Output("monthly-heatmap", "figure"),
    Input("year-range", "value"),
    Input("label-toggle", "value"),
)
def update_performance(year_range, label_toggle):
    start_year, end_year = normalize_year_range(
        year_range, int(yearly_df.index.min()), int(yearly_df.index.max())
    )
    visible_years = yearly_df.loc[(yearly_df.index >= start_year) & (yearly_df.index <= end_year)].copy()
    colors = ["#E50914" if value < 0 else "#2ECC71" for value in visible_years["Return_Pct"]]
    text = visible_years["Return_Pct"].round(1).astype(str) + "%"

    annual_fig = go.Figure(
        go.Bar(
            x=visible_years.index.astype(str),
            y=visible_years["Return_Pct"].round(1),
            marker_color=colors,
            text=text if label_toggle == "show" else None,
            textposition="outside",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        )
    )
    annual_fig.add_hline(y=0, line_dash="solid", line_color="#1f2937", line_width=1)
    annual_fig.update_layout(
        title="Annual Return by Year",
        template="plotly_white",
        height=470,
        margin={"l": 40, "r": 24, "t": 70, "b": 40},
        xaxis_title="Year",
        yaxis_title="Annual Return",
        yaxis={"ticksuffix": "%"},
    )

    selected_df = df[(df["Year"] >= start_year) & (df["Year"] <= end_year)]
    pivot = selected_df.pivot_table(values="Daily_Return", index="Year", columns="Month", aggfunc="sum")
    pivot = pivot.reindex(columns=range(1, 13))
    pivot.columns = MONTH_NAMES

    heatmap_fig = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        aspect="auto",
        labels={"x": "Month", "y": "Year", "color": "Return (%)"},
    )
    heatmap_height = max(430, min(620, 140 + len(pivot) * 18))
    heatmap_fig.update_layout(
        title="Monthly Cumulative Return Heatmap",
        template="plotly_white",
        height=heatmap_height,
        margin={"l": 40, "r": 24, "t": 70, "b": 40},
        yaxis={"tickmode": "array", "tickvals": list(pivot.index), "ticktext": [str(year) for year in pivot.index]},
    )

    best_year = visible_years["Return_Pct"].idxmax()
    worst_year = visible_years["Return_Pct"].idxmin()
    positive_years = int((visible_years["Return_Pct"] > 0).sum())
    cards = [
        metric_card("Best year", f"{best_year}", pct(visible_years.loc[best_year, "Return_Pct"])),
        metric_card("Worst year", f"{worst_year}", pct(visible_years.loc[worst_year, "Return_Pct"])),
        metric_card("Positive years", f"{positive_years} of {len(visible_years)}", "Years with a gain"),
        metric_card("Average annual return", pct(visible_years["Return_Pct"].mean()), "Within selected range"),
    ]
    return cards, annual_fig, heatmap_fig


@app.callback(
    Output("risk-cards", "children"),
    Output("crash-chart", "figure"),
    Output("risk-chart", "figure"),
    Input("period-selector", "value"),
    Input("vol-window", "value"),
    Input("return-bins", "value"),
)
def update_risk(period_key, vol_window, return_bins):
    period_key = period_key or "crash"
    vol_window = int(vol_window or 30)
    bin_count = max(20, min(int(return_bins or 80), 120))
    label, start, end = PERIODS[period_key]
    start = pd.to_datetime(start or df.index.min())
    end = pd.to_datetime(end or df.index.max())
    focus = df.loc[(df.index >= start) & (df.index <= end)].copy()
    focus[f"Volatility_{vol_window}"] = focus["Daily_Return"].rolling(vol_window).std()

    weekly = (
        focus.resample("W")
        .agg(Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"), Close=("Close", "last"), Volume=("Volume", "sum"))
        .dropna()
    )

    crash_fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        subplot_titles=["Price (Weekly Candles)", "Volume"],
    )
    crash_fig.add_trace(
        go.Candlestick(
            x=weekly.index,
            open=weekly["Open"],
            high=weekly["High"],
            low=weekly["Low"],
            close=weekly["Close"],
            name="NFLX",
            increasing_line_color="#2ECC71",
            decreasing_line_color="#E50914",
        ),
        row=1,
        col=1,
    )
    crash_fig.add_trace(
        go.Bar(x=weekly.index, y=weekly["Volume"] / 1e6, name="Volume (M)", marker_color="#4A90E2", opacity=0.65),
        row=2,
        col=1,
    )

    peak_date = focus["Close"].idxmax()
    trough_date = focus["Close"].idxmin()
    crash_fig.add_annotation(
        x=peak_date,
        y=float(focus.loc[peak_date, "High"]) * 1.05,
        text=f"Peak {money(focus.loc[peak_date, 'Close'])}",
        showarrow=True,
        arrowhead=2,
        row=1,
        col=1,
        font={"color": "#117a37", "size": 12},
    )
    crash_fig.add_annotation(
        x=trough_date,
        y=float(focus.loc[trough_date, "Low"]),
        text=f"Trough {money(focus.loc[trough_date, 'Close'])}",
        showarrow=True,
        arrowhead=2,
        ay=-40,
        row=1,
        col=1,
        font={"color": "#E50914", "size": 12},
    )
    crash_fig.update_layout(
        title=f"{label}: Price and Volume",
        template="plotly_white",
        height=560,
        showlegend=False,
        margin={"l": 40, "r": 24, "t": 80, "b": 40},
        xaxis_rangeslider_visible=False,
    )
    crash_fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    crash_fig.update_yaxes(title_text="Volume (M)", row=2, col=1)

    returns = focus["Daily_Return"].dropna()
    return_min = float(returns.min())
    return_max = float(returns.max())
    bin_size = (return_max - return_min) / bin_count
    risk_fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[f"Daily Return Distribution ({bin_count} bins)", f"{vol_window}-Day Rolling Volatility"],
    )
    risk_fig.add_trace(
        go.Histogram(
            x=returns,
            nbinsx=bin_count,
            xbins={"start": return_min, "end": return_max, "size": bin_size},
            marker_color="#4A90E2",
            opacity=0.75,
            name="Daily Returns",
            hovertemplate="Return: %{x:.1f}%<br>Count: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    risk_fig.add_trace(
        go.Scatter(
            x=focus.index,
            y=focus[f"Volatility_{vol_window}"],
            name="Rolling Volatility",
            fill="tozeroy",
            line={"color": "#E50914", "width": 1.2},
            fillcolor="rgba(229,9,20,0.15)",
            hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )
    risk_fig.update_layout(
        title="Netflix Risk Profile",
        template="plotly_white",
        height=450,
        showlegend=False,
        margin={"l": 40, "r": 24, "t": 80, "b": 40},
    )
    risk_fig.update_xaxes(title_text="Daily Return (%)", row=1, col=1)
    risk_fig.update_yaxes(title_text="Frequency", row=1, col=1)
    risk_fig.update_xaxes(title_text="Date", row=1, col=2)
    risk_fig.update_yaxes(title_text="Std Dev (%)", row=1, col=2)

    drop = (focus["Close"].min() / focus["Close"].max() - 1) * 100
    cards = [
        metric_card("Period", label, f"{focus.index.min().date()} to {focus.index.max().date()}"),
        metric_card("Largest close", money(focus["Close"].max()), f"On {focus['Close'].idxmax().date()}"),
        metric_card("Lowest close", money(focus["Close"].min()), f"On {focus['Close'].idxmin().date()}"),
        metric_card("Peak-to-low move", pct(drop), "Within selected period"),
    ]
    return cards, crash_fig, risk_fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Netflix stock dashboard.")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on. Default: 8050.")
    parser.add_argument("--debug", action="store_true", help="Run Dash in debug mode.")
    args = parser.parse_args()

    app.run(debug=args.debug, port=args.port)
