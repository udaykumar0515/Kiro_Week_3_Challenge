"""
Data Weaver Dashboard - Weather vs Search Trends Correlation
A Streamlit dashboard that reveals hidden correlations between weather patterns and search behavior.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from weather_fetcher import WeatherFetcher
from trends_fetcher import TrendsFetcher
from data_processor import (
    process_weather_data,
    merge_weather_trends,
    calculate_correlation,
    calculate_linear_regression,
    get_regression_line,
    interpret_correlation
)

# Page configuration
st.set_page_config(
    page_title="Data Weaver - Weather vs Trends",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved readability and design
st.markdown("""
<style>
    /* Main background gradient - softer for better readability */
    .stApp {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    /* Improved text contrast */
    p, div, span, label {
        color: white !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Card styling */
    .css-1r6slb0 {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric styling - better visibility */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    
    /* Headers - improved contrast */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    }
    
    /* Sidebar - better contrast */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(120deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🌦️ Data Weaver: Weather vs Search Trends")
st.markdown("""
<div style='background: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; margin-bottom: 30px;'>
    <p style='color: white; font-size: 1.1rem; margin: 0;'>
        Discover hidden correlations between weather patterns and search behavior. 
        This dashboard mashes up <strong>Open-Meteo weather data</strong> with <strong>Google Trends</strong> 
        to reveal fascinating insights about how the weather influences what we search for.
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize fetchers
@st.cache_resource
def get_fetchers():
    return WeatherFetcher(), TrendsFetcher()

weather_fetcher, trends_fetcher = get_fetchers()

# Sidebar controls
st.sidebar.header("⚙️ Configuration")

# Location presets
location_presets = {
    "London, UK": (51.5074, -0.1278),
    "New York, USA": (40.7128, -74.0060),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Mumbai, India": (19.0760, 72.8777),
    "Sydney, Australia": (-33.8688, 151.2093),
}

selected_location = st.sidebar.selectbox(
    "📍 Select Location",
    options=list(location_presets.keys()),
    index=0
)

latitude, longitude = location_presets[selected_location]

# Keyword suggestions based on weather relevance
keyword_suggestions = [
    "umbrella",
    "ice cream",
    "heating",
    "air conditioning",
    "sunscreen",
    "rain boots",
    "cold medicine",
    "beach",
    "indoor activities",
    "hot chocolate"
]

selected_keyword = st.sidebar.selectbox(
    "🔍 Search Keyword",
    options=keyword_suggestions,
    index=0
)

# Date range
st.sidebar.subheader("📅 Date Range")
date_presets = {
    "Last 30 days": 30,
    "Last 60 days": 60,
    "Last 90 days": 90,
}

selected_preset = st.sidebar.selectbox(
    "Select Preset",
    options=list(date_presets.keys()),
    index=2
)

days_back = date_presets[selected_preset]
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

st.sidebar.info(f"Analyzing data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Weather metric selection
weather_metrics = {
    "Temperature (°C)": ("temperature", "mean"),
    "Precipitation (mm)": ("precipitation", "sum"),
    "Cloud Cover (%)": ("cloudcover", "mean"),
    "Wind Speed (km/h)": ("windspeed", "mean"),
}

selected_metric = st.sidebar.selectbox(
    "🌡️ Weather Metric",
    options=list(weather_metrics.keys()),
    index=0
)

weather_column, weather_agg = weather_metrics[selected_metric]

# Fetch button
fetch_button = st.sidebar.button("🚀 Fetch & Analyze Data", use_container_width=True)

# Clear cache buttons
col1, col2 = st.sidebar.columns(2)
if col1.button("🗑️ Clear Weather Cache", use_container_width=True):
    weather_fetcher.clear_cache()
    st.sidebar.success("Weather cache cleared!")

if col2.button("🗑️ Clear Trends Cache", use_container_width=True):
    trends_fetcher.clear_cache()
    st.sidebar.success("Trends cache cleared!")

# Main content
if fetch_button or 'data_loaded' in st.session_state:
    
    with st.spinner("🔄 Fetching weather data..."):
        weather_data = weather_fetcher.fetch_weather_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
    
    if weather_data is None:
        st.error("❌ Failed to fetch weather data. Please try again.")
        st.stop()
    
    with st.spinner("🔄 Fetching Google Trends data..."):
        trends_data = trends_fetcher.fetch_trends_data(
            keyword=selected_keyword,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            geo=''  # Worldwide
        )
    
    if trends_data is None:
        st.error("❌ Failed to fetch trends data. This may be due to rate limiting. Please wait a few minutes and try again.")
        st.stop()
    
    # Process data
    with st.spinner("📊 Processing and analyzing data..."):
        weather_df = process_weather_data(weather_data)
        merged_df = merge_weather_trends(
            weather_df,
            trends_data,
            weather_column=weather_column,
            weather_agg=weather_agg
        )
    
    st.session_state['data_loaded'] = True
    st.session_state['merged_df'] = merged_df
    st.session_state['weather_column'] = weather_column
    st.session_state['selected_metric'] = selected_metric
    st.session_state['selected_keyword'] = selected_keyword
    
    # Get data from session state
    merged_df = st.session_state.get('merged_df')
    weather_column = st.session_state.get('weather_column')
    selected_metric = st.session_state.get('selected_metric')
    selected_keyword = st.session_state.get('selected_keyword')
    
    if merged_df is not None and not merged_df.empty:
        
        # Calculate statistics
        trends_col = merged_df.columns[1]  # Second column is trends data
        corr, pval = calculate_correlation(merged_df, weather_column, trends_col)
        regression = calculate_linear_regression(merged_df, weather_column, trends_col)
        interpretation = interpret_correlation(corr, pval)
        
        # Display key metrics
        st.markdown("### 📊 Key Insights")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "Correlation",
            f"{corr:.3f}",
            delta="Strong" if abs(corr) > 0.7 else ("Moderate" if abs(corr) > 0.3 else "Weak")
        )
        
        col2.metric(
            "P-Value",
            f"{pval:.4f}",
            delta="Significant" if pval < 0.05 else "Not Significant"
        )
        
        col3.metric(
            "R² Score",
            f"{regression['r_squared']:.3f}",
            delta=f"{regression['r_squared']*100:.1f}% variance"
        )
        
        col4.metric(
            "Data Points",
            len(merged_df),
            delta=f"{len(merged_df)} days"
        )
        
        # Interpretation panel
        st.markdown("### 🔍 Statistical Interpretation")
        st.info(interpretation)
        
        # Visualizations
        st.markdown("### 📈 Visualizations")
        
        # Tab layout for charts
        tab1, tab2, tab3 = st.tabs(["📉 Time Series Overlay", "📊 Scatter & Regression", "📋 Data Table"])
        
        with tab1:
            # Time series overlay plot
            fig_timeseries = go.Figure()
            
            # Weather data
            fig_timeseries.add_trace(go.Scatter(
                x=merged_df.index,
                y=merged_df[weather_column],
                name=selected_metric,
                line=dict(color='#00D9FF', width=4),  # Bright cyan
                yaxis='y1',
                hovertemplate='%{x|%Y-%m-%d}<br>' + selected_metric + ': %{y:.2f}<extra></extra>'
            ))
            
            # Trends data (on secondary axis)
            fig_timeseries.add_trace(go.Scatter(
                x=merged_df.index,
                y=merged_df[trends_col],
                name=f'Search Interest: {selected_keyword}',
                line=dict(color='#FFD700', width=4, dash='solid'),  # Bright gold/yellow
                yaxis='y2',
                hovertemplate='%{x|%Y-%m-%d}<br>Search Interest: %{y}<extra></extra>'
            ))
            
            fig_timeseries.update_layout(
                title=dict(
                    text=f"{selected_metric} vs Search Interest for '{selected_keyword}'",
                    font=dict(size=18, color='white')
                ),
                xaxis=dict(
                    title=dict(text="Date", font=dict(color='white', size=14)),
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='white', size=12)
                ),
                yaxis=dict(
                    title=dict(text=selected_metric, font=dict(color='#00D9FF', size=14)),  # Bright cyan
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='white', size=12)
                ),
                yaxis2=dict(
                    title=dict(text=f"Search Interest: {selected_keyword}", font=dict(color='#FFD700', size=14)),  # Bright yellow
                    overlaying='y',
                    side='right',
                    tickfont=dict(color='white', size=12)
                ),
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=12),
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='white', size=12)
                )
            )
            
            st.plotly_chart(fig_timeseries, use_container_width=True)
        
        with tab2:
            # Scatter plot with regression line
            fig_scatter = go.Figure()
            
            # Scatter points
            fig_scatter.add_trace(go.Scatter(
                x=merged_df[weather_column],
                y=merged_df[trends_col],
                mode='markers',
                name='Data Points',
                marker=dict(
                    size=10,
                    color=merged_df[trends_col],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Search<br>Interest"),
                    line=dict(width=1, color='white')
                ),
                hovertemplate=selected_metric + ': %{x:.2f}<br>Search Interest: %{y}<extra></extra>'
            ))
            
            # Regression line
            regression_y = get_regression_line(merged_df, weather_column, regression)
            fig_scatter.add_trace(go.Scatter(
                x=merged_df[weather_column],
                y=regression_y,
                mode='lines',
                name=f'Regression Line (R²={regression["r_squared"]:.3f})',
                line=dict(color='#ff6b6b', width=3, dash='dash'),
                hovertemplate='Predicted: %{y:.2f}<extra></extra>'
            ))
            
            fig_scatter.update_layout(
                title=dict(
                    text=f"Correlation: {selected_metric} vs Search for '{selected_keyword}'",
                    font=dict(size=18, color='white')
                ),
                xaxis=dict(
                    title=dict(text=selected_metric, font=dict(color='white', size=14)),
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='white', size=12)
                ),
                yaxis=dict(
                    title=dict(text=f"Search Interest: {selected_keyword}", font=dict(color='white', size=14)),
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='white', size=12)
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=12),
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='white', size=12)
                )
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Show regression equation
            st.markdown(f"""
            **Regression Equation:**  
            `Search Interest = {regression['slope']:.4f} × {selected_metric} + {regression['intercept']:.4f}`
            
            - **Slope:** {regression['slope']:.4f} (change in search interest per unit of {weather_column})
            - **Intercept:** {regression['intercept']:.4f}
            - **Standard Error:** {regression['std_err']:.4f}
            """)
        
        with tab3:
            # Data table
            st.markdown("#### 📋 Raw Data")
            
            # Display options
            display_df = merged_df.copy()
            display_df.index = display_df.index.strftime('%Y-%m-%d')
            display_df = display_df.reset_index()
            display_df.columns = ['Date', selected_metric, f'Search: {selected_keyword}']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = merged_df.to_csv()
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"weather_trends_{selected_keyword}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# Methodology section
with st.expander("📖 Methodology & About"):
    st.markdown("""
    ### How This Works
    
    **Data Weaver** combines two unrelated public data sources to discover interesting correlations:
    
    1. **Weather Data** from [Open-Meteo](https://open-meteo.com/)
       - Free, open-source weather API
       - Hourly historical weather data (temperature, precipitation, cloud cover, wind speed)
       - License: CC BY 4.0
    
    2. **Search Trends** from Google Trends (via pytrends library)
       - Search interest over time for specific keywords
       - Normalized to 0-100 scale
       - Worldwide or region-specific data
    
    ### Statistical Analysis
    
    - **Correlation Coefficient (r):** Measures the strength and direction of linear relationship (-1 to +1)
    - **P-Value:** Tests statistical significance (p < 0.05 indicates significant correlation)
    - **Linear Regression:** Models the relationship with y = mx + b
    - **R² Score:** Proportion of variance in search interest explained by weather (0 to 1)
    
    ### Caching Strategy
    
    - Weather data cached for 24 hours
    - Trends data cached for 7 days
    - Reduces API calls and improves performance
    - Clear cache buttons available in sidebar
    
    ### Built With
    
    - **Streamlit** - Interactive dashboard framework
    - **Plotly** - Interactive visualizations
    - **Pandas** - Data processing
    - **SciPy** - Statistical analysis
    - **Requests** - HTTP client for APIs
    
    ---
    
    **Created for Kiro Week 3 Challenge** | [GitHub Repository](https://github.com/udaykumar0515/Kiro_Week_3_Challenge)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.7);'>
    <p>🌦️ Data Weaver Dashboard | Week 3 - "The Data Weaver" Challenge</p>
    <p>Built with Streamlit + Open-Meteo + Google Trends | 
    <a href='https://github.com/udaykumar0515/Kiro_Week_3_Challenge' style='color: white;'>GitHub</a></p>
</div>
""", unsafe_allow_html=True)
