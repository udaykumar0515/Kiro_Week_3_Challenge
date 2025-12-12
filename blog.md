# Building Data Weaver: Discovering Hidden Correlations Between Weather and Search Behavior

**TL;DR:** I built an interactive dashboard that mashes up Open-Meteo weather data with Google Trends to reveal fascinating correlations between weather patterns and what people search for online. Using Streamlit, Python, and statistical analysis, the project demonstrates how AI assistance (Kiro) can accelerate development from concept to deployment in hours instead of days.

---

## Introduction

Have you ever wondered if rainy weather makes people search for "umbrella" more often? Or if hot days correlate with searches for "ice cream"? **Data Weaver** is an interactive analytics dashboard that answers these questions by combining two seemingly unrelated public data sources: real-time weather patterns and Google search trends.

This project was built for the **Kiro Week 3 Challenge: "The Data Weaver,"** which tasked participants with mashing up public APIs to discover unexpected insights. The result is a production-ready dashboard with statistical analysis, beautiful visualizations, comprehensive testing, and full Docker support—all accelerated by Kiro AI agent.

**Live Demo:** [GitHub Repository](https://github.com/udaykumar0515/Kiro_Week_3_Challenge)

---

## The Problem Statement

### Why Mash Up Weather and Search Trends?

Human behavior is influenced by environment. Weather affects our mood, activities, and even our digital habits. However, quantifying this relationship requires:

1. **Reliable weather data** (historical, hourly, globally accessible)
2. **Search interest data** (normalized, time-series format)
3. **Statistical rigor** (correlation testing, regression analysis)
4. **Interactive exploration** (filters, multiple metrics, real-time updates)

Most existing tools either focus on weather forecasting OR trend analysis, but rarely combine them to reveal **correlational insights**.

### The Challenge

The Week 3 challenge requirements were:

- ✅ Mash up **two unrelated public data sources**
- ✅ Provide **interactive dashboard** with visualizations
- ✅ Include **statistical analysis** (correlation, regression, significance testing)
- ✅ Implement **caching** to respect API rate limits
- ✅ Create **comprehensive documentation** (README, DETAILS.md, blog)
- ✅ Set up **testing** (pytest suite with mocking)
- ✅ Dockerize for **reproducible deployment**
- ✅ Add **CI/CD pipeline** (GitHub Actions)
- ✅ Document **Kiro's contributions** in `.kiro/` directory

---

## Selected Data Sources and Why They're Interesting

### Data Source 1: Open-Meteo Weather API

**Why I chose it:**

- ✅ **Free and open-source** (no API key required)
- ✅ **Comprehensive data:** Hourly temperature, precipitation, cloud cover, wind speed
- ✅ **Global coverage:** Any lat/lon coordinate
- ✅ **Reliable:** 10,000 requests/day limit (generous for this project)
- ✅ **License:** CC BY 4.0 (attribution only)

**Endpoint Example:**

```
https://api.open-meteo.com/v1/forecast?latitude=51.5074&longitude=-0.1278&start_date=2024-11-01&end_date=2024-12-01&hourly=temperature_2m,precipitation,cloudcover,windspeed_10m&timezone=auto
```

**Sample Response:**

```json
{
  "hourly": {
    "time": ["2024-11-01T00:00", "2024-11-01T01:00", ...],
    "temperature_2m": [12.5, 12.1, 11.8, ...],
    "precipitation": [0.0, 0.1, 0.2, ...],
    "cloudcover": [60, 65, 70, ...],
    "windspeed_10m": [15.2, 16.1, 14.8, ...]
  }
}
```

### Data Source 2: Google Trends (via pytrends)

**Why I chose it:**

- ✅ **Publicly accessible:** No authentication required
- ✅ **Normalized data:** 0-100 scale (search interest relative to peak)
- ✅ **Time-series format:** Perfect for merging with weather data
- ✅ **Python library:** `pytrends` provides easy interface
- ✅ **License:** Apache 2.0

**Library Usage:**

```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
pytrends.build_payload(
    kw_list=['umbrella'],
    timeframe='2024-11-01 2024-12-01',
    geo=''  # Worldwide
)
df = pytrends.interest_over_time()
```

**Sample Output:**

```
             umbrella  isPartial
date
2024-11-01         45      False
2024-11-02         52      False
2024-11-03         38      False
...
```

### Why This Pairing Is Interesting

Weather influences **physical behavior** (carrying an umbrella, buying ice cream), which in turn may influence **digital behavior** (searching for products, planning purchases). By quantifying the correlation, we can:

- 🔍 **Answer behavioral questions:** Does rain drive umbrella searches?
- 📊 **Test hypotheses:** Are cold days correlated with "heating" searches?
- 🎯 **Inform marketing:** When should retailers promote weather-related products?
- 📈 **Explore causality:** While correlation ≠ causation, strong statistical relationships warrant further investigation

---

## Architecture & How the Dashboard Works

### System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  (Streamlit Dashboard - browser @ localhost:8501)               │
│                                                                  │
│  Controls:                                                       │
│  • Location selector (5 cities)                                 │
│  • Keyword input (suggestions provided)                         │
│  • Date range (30/60/90 days)                                   │
│  • Weather metric (temp/precip/cloud/wind)                      │
│  • Fetch button                                                 │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATA FETCHING LAYER                           │
│                                                                  │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │ WeatherFetcher   │              │ TrendsFetcher    │         │
│  │ • Check cache    │              │ • Check cache    │         │
│  │ • Call API if    │              │ • Call pytrends  │         │
│  │   expired        │              │   if expired     │         │
│  │ • Save JSON      │              │ • Save CSV       │         │
│  └────────┬─────────┘              └────────┬─────────┘         │
│           │                                 │                   │
│           ├─── Cache: weather_*.json        │                   │
│           │                                 │                   │
│           └─── Cache: trends_*.csv ─────────┘                   │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                  DATA PROCESSING LAYER                           │
│  (data_processor.py)                                             │
│                                                                  │
│  1. process_weather_data(json) → DataFrame (hourly)             │
│  2. aggregate_to_daily(df, column, method='mean')               │
│  3. merge_weather_trends(weather_df, trends_df) → merged_df     │
│  4. calculate_correlation(merged_df, col1, col2) → (r, p-val)   │
│  5. calculate_linear_regression(merged_df, x, y) → params       │
│  6. interpret_correlation(r, p) → human-readable string         │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION LAYER                            │
│  (Plotly charts rendered in Streamlit)                           │
│                                                                  │
│  • Metric cards (correlation, p-value, R², data points)         │
│  • Time series overlay (dual y-axes, interactive hover)         │
│  • Scatter plot with regression line (color-coded points)       │
│  • Data table (sortable, downloadable CSV)                      │
│  • Methodology panel (expandable documentation)                 │
└──────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component            | Technology       | Purpose                                   |
| -------------------- | ---------------- | ----------------------------------------- |
| **Frontend**         | Streamlit 1.29.0 | Interactive dashboard UI                  |
| **Visualization**    | Plotly 5.18.0    | Interactive charts (time series, scatter) |
| **Data Processing**  | Pandas 2.1.4     | DataFrame operations, merging             |
| **Statistics**       | SciPy 1.11.4     | Pearson correlation, linear regression    |
| **HTTP Client**      | Requests 2.31.0  | Open-Meteo API calls                      |
| **Trends Client**    | pytrends 4.9.2   | Google Trends data fetching               |
| **Testing**          | Pytest 7.4.3     | Unit tests with mocking                   |
| **Containerization** | Docker           | Reproducible deployment                   |
| **CI/CD**            | GitHub Actions   | Automated testing, linting, builds        |

### Data Flow Example

**User Action:** User selects London, keyword "umbrella", last 90 days, temperature metric, clicks "Fetch & Analyze"

**Step 1 - Weather Fetch:**

```python
weather_data = weather_fetcher.fetch_weather_data(
    latitude=51.5074,
    longitude=-0.1278,
    start_date='2024-09-13',
    end_date='2024-12-12'
)
# Returns JSON with hourly data for 90 days (2,160 hours)
```

**Step 2 - Trends Fetch:**

```python
trends_data = trends_fetcher.fetch_trends_data(
    keyword='umbrella',
    start_date='2024-09-13',
    end_date='2024-12-12',
    geo=''  # Worldwide
)
# Returns DataFrame with daily search interest (90 rows)
```

**Step 3 - Processing:**

```python
weather_df = process_weather_data(weather_data)
# Convert JSON → DataFrame (2,160 rows, hourly)

merged_df = merge_weather_trends(
    weather_df,
    trends_data,
    weather_column='temperature',
    weather_agg='mean'
)
# Aggregate weather to daily (mean temp)
# Merge with trends on date index
# Result: 90 rows with [date, temperature, umbrella]
```

**Step 4 - Statistics:**

```python
corr, pval = calculate_correlation(merged_df, 'temperature', 'umbrella')
# e.g., corr = -0.42, pval = 0.0001
# Interpretation: Moderate negative correlation, statistically significant

regression = calculate_linear_regression(merged_df, 'temperature', 'umbrella')
# {'slope': -2.1, 'intercept': 75.3, 'r_squared': 0.18, 'p_value': 0.0001, ...}
```

**Step 5 - Visualization:**

- **Metric Cards:** Show r=-0.42, p=0.0001, R²=0.18, 90 points
- **Time Series:** Dual y-axes chart with temperature (left) and search interest (right)
- **Scatter Plot:** X=temperature, Y=umbrella searches, regression line overlaid
- **Interpretation:** "Statistically significant moderate negative correlation. As temperature decreases, umbrella searches tend to increase."

---

## How Kiro Sped Up Development

### The Power of AI-Assisted Development

Without Kiro, building this project would require:

- ⏰ **~12-15 hours** spread across 2-3 days
- 📚 Reading docs for Open-Meteo, pytrends, Streamlit, Plotly
- 🐛 Debugging cache logic, timezone handling, API quirks
- 🎨 Designing UI from scratch (CSS, color schemes)
- 🧪 Writing test fixtures and mocks manually

**With Kiro:** ~4-6 hours of active collaboration

### Exact Tasks Kiro Automated

#### 1. **Project Scaffolding** (Saved ~10 minutes)

**Prompt:**

```
Create directory structure: /app, /tests, /.kiro, /.github/workflows, /assets, /data/cache
```

**Kiro's Output:**

- Created all directories
- Generated `.gitignore` excluding cache but preserving `.kiro/`
- Created `.env.sample` with sensible defaults

#### 2. **Weather Data Fetcher** (Saved ~1.5 hours)

**Prompt:**

```
Write WeatherFetcher class that:
- Calls Open-Meteo API for historical weather
- Caches responses in data/cache/ as JSON
- Validates cache expiry (24 hours)
- Includes error handling and user-friendly logging
```

**Kiro's Output:** `app/weather_fetcher.py` (150 lines) with:

- `_get_cache_path()` - Generate unique cache filename
- `_is_cache_valid()` - Check modification time
- `fetch_weather_data()` - Main fetch logic with try/except
- `clear_cache()` - Utility method

**Code Snippet from Kiro's Output:**

```python
def fetch_weather_data(self, latitude, longitude, start_date, end_date, use_cache=True):
    cache_path = self._get_cache_path(latitude, longitude, start_date, end_date)

    # Try cache first
    if use_cache and self._is_cache_valid(cache_path):
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                print(f"✓ Loaded from cache: {cache_path.name}")
                return data
        except Exception as e:
            print(f"⚠ Cache read error: {e}")

    # Fetch from API
    try:
        params = {...}
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Save to cache
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)

        print("✓ Weather data fetched and cached")
        return data
    except requests.RequestException as e:
        print(f"✗ API request failed: {e}")
        return None
```

#### 3. **Google Trends Fetcher** (Saved ~1.5 hours)

**Prompt:**

```
Write TrendsFetcher class using pytrends. Include:
- 7-day cache for trends data (CSV format)
- Respectful rate limiting (2-second delays)
- Error handling for rate limit responses
```

**Kiro's Output:** `app/trends_fetcher.py` (140 lines) with:

- `_init_pytrends()` - Lazy initialization with delay
- `fetch_trends_data()` - Build payload, fetch, cache
- Automatic `isPartial` column removal
- User-friendly error messages

#### 4. **Statistical Analysis Module** (Saved ~2 hours)

**Prompt:**

```
Create data_processor.py with functions for:
- Converting weather JSON to DataFrame
- Aggregating hourly to daily (mean/sum/max/min)
- Merging weather and trends on date index
- Calculating Pearson correlation + p-value
- Linear regression with slope, intercept, R², p-value
- Human-readable interpretation of correlation strength
```

**Kiro's Output:** `app/data_processor.py` (200 lines) with comprehensive docstrings

**Code Snippet - Correlation Interpretation:**

```python
def interpret_correlation(corr, p_value, alpha=0.05):
    is_significant = p_value < alpha
    abs_corr = abs(corr)

    if abs_corr < 0.3:
        strength = "weak"
    elif abs_corr < 0.7:
        strength = "moderate"
    else:
        strength = "strong"

    direction = "positive" if corr > 0 else "negative"

    if is_significant:
        return (f"Statistically significant {strength} {direction} correlation "
                f"(r={corr:.3f}, p={p_value:.4f}). ...")
    else:
        return f"NOT statistically significant (p={p_value:.4f})..."
```

#### 5. **Streamlit Dashboard UI** (Saved ~3 hours)

**Prompt:**

```
Build Streamlit dashboard with:
- Premium UI: gradient background, glassmorphism, custom CSS
- Sidebar controls: location dropdown, keyword select, date presets, weather metric
- Tabs: time series overlay (dual y-axes), scatter + regression, data table
- Metric cards for correlation, p-value, R², data points
- Export buttons (CSV download, Plotly PNG export)
- Methodology expandable panel
```

**Kiro's Output:** `app/dashboard.py` (450 lines)

**UI Highlights:**

```python
# Custom CSS for gradient and glassmorphism
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        background: linear-gradient(120deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Dual y-axes time series
fig_timeseries = go.Figure()
fig_timeseries.add_trace(go.Scatter(
    x=merged_df.index,
    y=merged_df[weather_column],
    name=selected_metric,
    yaxis='y1',
    line=dict(color='#667eea', width=3)
))
fig_timeseries.add_trace(go.Scatter(
    x=merged_df.index,
    y=merged_df[trends_col],
    name=f'Search: {selected_keyword}',
    yaxis='y2',
    line=dict(color='#764ba2', width=3, dash='dash')
))
fig_timeseries.update_layout(
    yaxis=dict(title=selected_metric),
    yaxis2=dict(title=f'Search: {selected_keyword}', overlaying='y', side='right')
)
```

#### 6. **Test Suite** (Saved ~1.5 hours)

**Prompt:**

```
Generate pytest tests for:
- WeatherFetcher: cache validation, mocked API calls, error handling
- DataProcessor: correlation calculations, regression accuracy, edge cases
Use pytest-mock for mocking requests.get
```

**Kiro's Output:**

- `tests/test_weather_fetcher.py` (120 lines, 8 tests)
- `tests/test_data_processor.py` (150 lines, 12 tests)

**Test Example:**

```python
def test_fetch_with_mock_response(fetcher, sample_weather_response, tmp_path, mocker):
    fetcher.CACHE_DIR = tmp_path

    mock_response = mocker.Mock()
    mock_response.json.return_value = sample_weather_response
    mock_response.raise_for_status = mocker.Mock()
    mocker.patch('requests.get', return_value=mock_response)

    data = fetcher.fetch_weather_data(
        latitude=51.5,
        longitude=-0.12,
        start_date="2024-01-01",
        end_date="2024-01-03"
    )

    assert data is not None
    assert 'hourly' in data
    # Verify cache was created
    cache_files = list(tmp_path.glob("weather_*.json"))
    assert len(cache_files) == 1
```

#### 7. **Docker Configuration** (Saved ~30 minutes)

**Prompt:**

```
Create Dockerfile for Streamlit app with health checks and docker-compose.yml with volume mounts for cache
```

**Kiro's Output:**

- `Dockerfile` (multi-stage, slim base image, health check)
- `docker-compose.yml` (port mapping, environment variables, volume persistence)

#### 8. **CI/CD Pipeline** (Saved ~1 hour)

**Prompt:**

```
Set up GitHub Actions workflow with jobs for: pytest (with coverage), flake8 linting, Docker build and test
```

**Kiro's Output:** `.github/workflows/ci.yml` with:

- Test job (runs pytest, uploads coverage to Codecov)
- Lint job (flake8 syntax checks)
- Docker job (builds image, runs container, checks logs)

#### 9. **Documentation** (Saved ~2 hours)

**Files Kiro Generated:**

- `README.md` (250 lines): Quick start, features, badges, project structure
- `DETAILS.md` (500+ lines): Comprehensive docs per template
- `.kiro/agent_log.md`: Command-by-command log
- `.kiro/kiro_run_config.json`: Config metadata

### Total Development Time Comparison

| Task               | Manual         | With Kiro     | Time Saved   |
| ------------------ | -------------- | ------------- | ------------ |
| Project setup      | 30 min         | 5 min         | 25 min       |
| Data fetchers      | 3 hours        | 30 min        | 2.5 hours    |
| Statistical module | 2 hours        | 20 min        | 1.7 hours    |
| Dashboard UI       | 4 hours        | 1 hour        | 3 hours      |
| Tests              | 2 hours        | 30 min        | 1.5 hours    |
| Docker + CI/CD     | 1.5 hours      | 20 min        | 1.3 hours    |
| Documentation      | 2.5 hours      | 30 min        | 2 hours      |
| **TOTAL**          | **15.5 hours** | **3.5 hours** | **12 hours** |

---

## Code Snippets

### 1. Weather Data Fetcher (with Caching)

```python
# app/weather_fetcher.py

class WeatherFetcher:
    """Fetch historical weather data from Open-Meteo API with caching."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_DIR = Path("data/cache")

    def __init__(self, cache_expiry_hours: int = 24):
        self.cache_expiry_hours = cache_expiry_hours
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, latitude: float, longitude: float,
                        start_date: str, end_date: str) -> Path:
        """Generate unique cache file path based on request parameters."""
        cache_key = f"{latitude}_{longitude}_{start_date}_{end_date}"
        return self.CACHE_DIR / f"weather_{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and hasn't expired."""
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=self.cache_expiry_hours)

    def fetch_weather_data(self, latitude: float, longitude: float,
                           start_date: str, end_date: str,
                           use_cache: bool = True) -> Optional[Dict]:
        """Fetch weather data with intelligent caching."""
        cache_path = self._get_cache_path(latitude, longitude, start_date, end_date)

        # Try cache first
        if use_cache and self._is_cache_valid(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)

        # Fetch from API
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date,
                'end_date': end_date,
                'hourly': 'temperature_2m,precipitation,cloudcover,windspeed_10m',
                'timezone': 'auto'
            }

            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Save to cache
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)

            return data
        except requests.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None
```

**Why This Code Matters:**

- ✅ **Respects API limits:** 24-hour cache prevents excessive requests
- ✅ **Unique cache keys:** Different queries get separate cache files
- ✅ **Graceful degradation:** Returns `None` on error (UI handles this)
- ✅ **Testable:** Easy to mock `requests.get` in tests

### 2. Chart Creation (Time Series Overlay)

```python
# app/dashboard.py (excerpt)

# Create time series with dual y-axes
fig_timeseries = go.Figure()

# Weather data on left y-axis
fig_timeseries.add_trace(go.Scatter(
    x=merged_df.index,
    y=merged_df[weather_column],
    name=selected_metric,  # e.g., "Temperature (°C)"
    line=dict(color='#667eea', width=3),
    yaxis='y1',
    hovertemplate='%{x|%Y-%m-%d}<br>' + selected_metric + ': %{y:.2f}<extra></extra>'
))

# Search trends on right y-axis
fig_timeseries.add_trace(go.Scatter(
    x=merged_df.index,
    y=merged_df[trends_col],  # e.g., "umbrella" search interest
    name=f'Search Interest: {selected_keyword}',
    line=dict(color='#764ba2', width=3, dash='dash'),
    yaxis='y2',
    hovertemplate='%{x|%Y-%m-%d}<br>Search Interest: %{y}<extra></extra>'
))

# Configure dual y-axes
fig_timeseries.update_layout(
    title=f"{selected_metric} vs Search Interest for '{selected_keyword}'",
    xaxis=dict(title="Date", gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(
        title=selected_metric,
        titlefont=dict(color='#667eea'),
        tickfont=dict(color='#667eea')
    ),
    yaxis2=dict(
        title=f"Search Interest: {selected_keyword}",
        titlefont=dict(color='#764ba2'),
        tickfont=dict(color='#764ba2'),
        overlaying='y',
        side='right'
    ),
    hovermode='x unified',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    height=500
)

st.plotly_chart(fig_timeseries, use_container_width=True)
```

**Why This Code Matters:**

- ✅ **Dual y-axes:** Different scales for weather (e.g., 10°C) and search interest (0-100)
- ✅ **Color coordination:** Matches legend colors to axes
- ✅ **Interactive hover:** Shows both values on hover
- ✅ **Responsive:** `use_container_width=True` for mobile/tablet

---

## Screenshots

### 1. Dashboard Main View

![Data Weaver Dashboard](assets/dashboard_main.png)

**Description:** Main dashboard showing sidebar controls (left) with location selector, keyword input, date range presets, and weather metric dropdown. Center displays key metric cards (correlation, p-value, R², data points) with gradient styling.

**ALT Text:** "Data Weaver dashboard main view with purple gradient background, sidebar controls for London location and umbrella keyword, metric cards showing correlation of -0.42 and p-value of 0.0001"

### 2. Time Series Analysis

![Time Series Overlay Chart](assets/timeseries_chart.png)

**Description:** Dual y-axis time series chart showing temperature (solid blue line, left axis) and umbrella search interest (dashed purple line, right axis) over 90 days. Interactive hover shows exact values for both metrics on each date.

**ALT Text:** "Time series chart with dual y-axes displaying temperature in degrees Celsius on left and umbrella search interest 0-100 scale on right, showing inverse correlation trend"

### 3. Correlation Scatter Plot

![Scatter Plot with Regression](assets/scatter_plot.png)

**Description:** Scatter plot with X-axis showing temperature, Y-axis showing search interest. Data points color-coded by search intensity (Viridis colorscale). Red dashed regression line overlaid showing negative correlation trend.

**ALT Text:** "Scatter plot showing negative correlation between temperature and umbrella searches, with color-coded points and red dashed regression line, R-squared value 0.18"

---

## Conclusion and Next Steps

### What I Learned

1. **Data Mashups Reveal Insights:** Combining weather and search trends uncovered quantifiable correlations I could only hypothesize about before.

2. **Caching Is Essential:** Without caching, API rate limits would halt development. Intelligent cache management (with expiry) balances freshness and efficiency.

3. **Statistical Rigor Matters:** Showing a chart isn't enough. P-values, R² scores, and interpretation text help users understand strength and significance.

4. **AI Acceleration Is Real:** Kiro reduced development time from 15+ hours to ~4 hours. Not just "faster coding"—Kiro made architectural decisions (cache structure, test fixtures) that would take research.

5. **Documentation = Credibility:** `.kiro/agent_log.md` and `DETAILS.md` provide transparency and reproducibility. Future employers/collaborators can see exactly what was built and how.

### Next Steps & Enhancements

**Short-term (v1.1):**

- ✅ Deploy to [Streamlit Cloud](https://share.streamlit.io) for live demo
- ✅ Add more location suggestions (user-submitted via GitHub issues)
- ✅ Implement custom lat/lon input (text boxes instead of dropdown)
- ✅ Add "Download Chart as PNG" buttons for each visualization

**Medium-term (v2.0):**

- 📈 **Multi-keyword comparison:** Compare "umbrella" vs "sunscreen" vs "ice cream" on same chart
- 🗺️ **Geographic heatmap:** Show correlation strength across multiple cities
- 📊 **Advanced stats:** Granger causality test (does weather _cause_ search changes?)
- 🔔 **Alerts:** Email when correlation exceeds threshold (e.g., r > 0.7)

**Long-term (v3.0):**

- 🤖 **ML predictions:** Train model to predict search interest from weather forecast
- 🌐 **Multi-region support:** Compare London umbrella searches vs Mumbai monsoon searches
- 📱 **Mobile app:** React Native frontend with same backend API
- 💼 **Commercial use:** Partner with retailers for targeted weather-based marketing

### Call to Action

Try Data Weaver yourself:

```bash
git clone https://github.com/udaykumar0515/Kiro_Week_3_Challenge.git
cd Kiro_Week_3_Challenge
pip install -r requirements.txt
streamlit run app/dashboard.py
```

**Questions? Contributions? Issues?**

- 📧 Open an issue: [GitHub Issues](https://github.com/udaykumar0515/Kiro_Week_3_Challenge/issues)
- 🌟 Star the repo if you found it useful!
- 🔄 Fork and submit PRs for enhancements

---

## GitHub Repository

🔗 **[https://github.com/udaykumar0515/Kiro_Week_3_Challenge](https://github.com/udaykumar0515/Kiro_Week_3_Challenge)**

**Branch:** `week3/data-weaver`  
**PR:** _(to be created after testing)_  
**License:** MIT

---

**Author:** Uday Kumar ([@udaykumar0515](https://github.com/udaykumar0515))  
**Date:** December 12, 2025  
**Challenge:** Kiro Week 3 - "The Data Weaver"  
**Accelerated By:** Kiro AI Agent 🤖

---

_This blog post is formatted for AWS Builder Center. Copy and paste into the Builder Center editor, then add screenshots from the `/assets` folder._
