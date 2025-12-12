"""
Data processing and analysis utilities.
Combines weather and trends data, performs statistical analysis.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional


def process_weather_data(weather_json: Dict) -> pd.DataFrame:
    """
    Convert Open-Meteo JSON response to pandas DataFrame.
    
    Args:
        weather_json: Raw JSON response from Open-Meteo API
        
    Returns:
        DataFrame with processed weather data
    """
    if not weather_json or 'hourly' not in weather_json:
        raise ValueError("Invalid weather data format")
    
    hourly = weather_json['hourly']
    
    df = pd.DataFrame({
        'time': pd.to_datetime(hourly['time']),
        'temperature': hourly['temperature_2m'],
        'precipitation': hourly['precipitation'],
        'cloudcover': hourly['cloudcover'],
        'windspeed': hourly['windspeed_10m']
    })
    
    df.set_index('time', inplace=True)
    
    return df


def aggregate_to_daily(df: pd.DataFrame, column: str, method: str = 'mean') -> pd.Series:
    """
    Aggregate hourly data to daily data.
    
    Args:
        df: DataFrame with hourly data
        column: Column name to aggregate
        method: Aggregation method ('mean', 'sum', 'max', 'min')
        
    Returns:
        Series with daily aggregated values
    """
    if method == 'mean':
        return df[column].resample('D').mean()
    elif method == 'sum':
        return df[column].resample('D').sum()
    elif method == 'max':
        return df[column].resample('D').max()
    elif method == 'min':
        return df[column].resample('D').min()
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def merge_weather_trends(
    weather_df: pd.DataFrame,
    trends_df: pd.DataFrame,
    weather_column: str = 'temperature',
    weather_agg: str = 'mean'
) -> pd.DataFrame:
    """
    Merge weather and trends data on daily basis.
    
    Args:
        weather_df: Weather data (hourly)
        trends_df: Trends data (daily or weekly)
        weather_column: Weather column to include
        weather_agg: How to aggregate weather data to daily
        
    Returns:
        DataFrame with both weather and trends data aligned by date
    """
    # Aggregate weather to daily
    weather_daily = aggregate_to_daily(weather_df, weather_column, weather_agg)
    weather_daily_df = weather_daily.to_frame(name=weather_column)
    
    # Get trends column name (should be the keyword)
    trends_column = trends_df.columns[0]
    
    # Merge on date index
    merged = weather_daily_df.join(trends_df[[trends_column]], how='inner')
    
    # Drop any NaN values
    merged = merged.dropna()
    
    return merged


def calculate_correlation(
    df: pd.DataFrame,
    col1: str,
    col2: str
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    
    Args:
        df: DataFrame containing both columns
        col1: First column name
        col2: Second column name
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    corr, pvalue = stats.pearsonr(df[col1], df[col2])
    return corr, pvalue


def calculate_linear_regression(
    df: pd.DataFrame,
    x_col: str,
    y_col: str
) -> Dict[str, float]:
    """
    Calculate linear regression parameters.
    
    Args:
        df: DataFrame containing both columns
        x_col: Independent variable column
        y_col: Dependent variable column
        
    Returns:
        Dictionary with regression parameters and statistics
    """
    x = df[x_col].values
    y = df[y_col].values
    
    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_err': std_err
    }


def get_regression_line(
    df: pd.DataFrame,
    x_col: str,
    regression_params: Dict[str, float]
) -> np.ndarray:
    """
    Generate y values for regression line.
    
    Args:
        df: DataFrame with x values
        x_col: Column name for x values
        regression_params: Regression parameters from calculate_linear_regression
        
    Returns:
        Array of y values for the regression line
    """
    x = df[x_col].values
    y = regression_params['slope'] * x + regression_params['intercept']
    return y


def interpret_correlation(corr: float, p_value: float, alpha: float = 0.05) -> str:
    """
    Provide human-readable interpretation of correlation.
    
    Args:
        corr: Correlation coefficient
        p_value: Statistical significance p-value
        alpha: Significance level (default 0.05)
        
    Returns:
        Interpretation string
    """
    # Check significance
    is_significant = p_value < alpha
    
    # Interpret strength
    abs_corr = abs(corr)
    if abs_corr < 0.3:
        strength = "weak"
    elif abs_corr < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    
    # Direction
    direction = "positive" if corr > 0 else "negative"
    
    # Build interpretation
    if is_significant:
        interpretation = f"There is a statistically significant {strength} {direction} correlation "
        interpretation += f"(r={corr:.3f}, p={p_value:.4f}). "
        
        if abs_corr < 0.3:
            interpretation += "The relationship is weak and may not be practically meaningful."
        elif abs_corr < 0.7:
            interpretation += "The variables show a moderate relationship."
        else:
            interpretation += "The variables are strongly related."
    else:
        interpretation = f"The correlation is NOT statistically significant (p={p_value:.4f}). "
        interpretation += "There is no reliable relationship between these variables."
    
    return interpretation


if __name__ == "__main__":
    # Test with sample data
    print("Data processing utilities loaded successfully!")
    
    # Create sample data for testing
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    sample_weather = pd.DataFrame({
        'temperature': np.random.randn(30) * 10 + 15,
    }, index=dates)
    
    sample_trends = pd.DataFrame({
        'search_interest': np.random.randint(20, 100, size=30)
    }, index=dates)
    
    # Test merge
    merged = merge_weather_trends(
        sample_weather.resample('H').ffill(),  # Simulate hourly
        sample_trends,
        'temperature',
        'mean'
    )
    
    print(f"\nMerged data shape: {merged.shape}")
    print(merged.head())
    
    # Test correlation
    corr, pval = calculate_correlation(merged, 'temperature', 'search_interest')
    print(f"\nCorrelation: {corr:.3f}, p-value: {pval:.4f}")
    print(interpret_correlation(corr, pval))
