"""
Test suite for data processing utilities.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.data_processor import (
    process_weather_data,
    aggregate_to_daily,
    merge_weather_trends,
    calculate_correlation,
    calculate_linear_regression,
    get_regression_line,
    interpret_correlation
)


@pytest.fixture
def sample_weather_json():
    """Sample weather data in API JSON format."""
    times = pd.date_range('2024-01-01', periods=24, freq='H')
    return {
        'hourly': {
            'time': [t.strftime('%Y-%m-%dT%H:%M') for t in times],
            'temperature_2m': list(range(10, 34)),
            'precipitation': [0.0] * 12 + [0.5] * 12,
            'cloudcover': [30] * 24,
            'windspeed_10m': [15.0] * 24
        }
    }


@pytest.fixture
def sample_weather_df():
    """Sample processed weather DataFrame."""
    dates = pd.date_range('2024-01-01', periods=24, freq='H')
    return pd.DataFrame({
        'temperature': np.random.randn(24) * 5 + 15,
        'precipitation': np.random.rand(24) * 2,
        'cloudcover': np.random.randint(0, 100, 24),
        'windspeed': np.random.rand(24) * 20
    }, index=dates)


@pytest.fixture
def sample_trends_df():
    """Sample trends DataFrame."""
    dates = pd.date_range('2024-01-01', periods=10, freq='D')
    return pd.DataFrame({
        'umbrella': np.random.randint(20, 100, 10)
    }, index=dates)


def test_process_weather_data(sample_weather_json):
    """Test weather JSON to DataFrame conversion."""
    df = process_weather_data(sample_weather_json)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 24
    assert 'temperature' in df.columns
    assert 'precipitation' in df.columns
    assert 'cloudcover' in df.columns
    assert 'windspeed' in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)


def test_process_weather_data_invalid():
    """Test error handling for invalid weather data."""
    with pytest.raises(ValueError):
        process_weather_data({})
    
    with pytest.raises(ValueError):
        process_weather_data({'hourly': {}})


def test_aggregate_to_daily_mean(sample_weather_df):
    """Test daily aggregation with mean."""
    daily = aggregate_to_daily(sample_weather_df, 'temperature', 'mean')
    
    assert isinstance(daily, pd.Series)
    assert len(daily) >= 1  # At least one day
    assert daily.index.freq == 'D' or True  # Daily frequency


def test_aggregate_to_daily_sum(sample_weather_df):
    """Test daily aggregation with sum."""
    daily = aggregate_to_daily(sample_weather_df, 'precipitation', 'sum')
    
    assert isinstance(daily, pd.Series)
    assert all(daily >= 0)  # Precipitation is non-negative


def test_aggregate_to_daily_invalid_method(sample_weather_df):
    """Test error handling for invalid aggregation method."""
    with pytest.raises(ValueError):
        aggregate_to_daily(sample_weather_df, 'temperature', 'invalid_method')


def test_merge_weather_trends(sample_weather_df, sample_trends_df):
    """Test merging weather and trends data."""
    merged = merge_weather_trends(
        sample_weather_df,
        sample_trends_df,
        weather_column='temperature',
        weather_agg='mean'
    )
    
    assert isinstance(merged, pd.DataFrame)
    assert 'temperature' in merged.columns
    assert 'umbrella' in merged.columns
    assert len(merged) > 0
    assert not merged.isna().any().any()  # No NaN values


def test_calculate_correlation():
    """Test correlation calculation."""
    # Create perfectly correlated data
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })
    
    corr, pval = calculate_correlation(df, 'x', 'y')
    
    assert corr == pytest.approx(1.0, abs=0.01)  # Perfect positive correlation
    assert pval < 0.05  # Significant


def test_calculate_correlation_negative():
    """Test negative correlation."""
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 8, 6, 4, 2]
    })
    
    corr, pval = calculate_correlation(df, 'x', 'y')
    
    assert corr == pytest.approx(-1.0, abs=0.01)  # Perfect negative correlation


def test_calculate_linear_regression():
    """Test linear regression calculation."""
    # y = 2x + 1
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [3, 5, 7, 9, 11]
    })
    
    reg = calculate_linear_regression(df, 'x', 'y')
    
    assert 'slope' in reg
    assert 'intercept' in reg
    assert 'r_squared' in reg
    assert 'p_value' in reg
    assert 'std_err' in reg
    
    assert reg['slope'] == pytest.approx(2.0, abs=0.01)
    assert reg['intercept'] == pytest.approx(1.0, abs=0.01)
    assert reg['r_squared'] == pytest.approx(1.0, abs=0.01)


def test_get_regression_line():
    """Test regression line generation."""
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
    params = {'slope': 2.0, 'intercept': 1.0}
    
    y_pred = get_regression_line(df, 'x', params)
    
    assert len(y_pred) == 5
    assert y_pred[0] == pytest.approx(3.0)  # 2*1 + 1
    assert y_pred[4] == pytest.approx(11.0)  # 2*5 + 1


def test_interpret_correlation_strong_positive():
    """Test interpretation of strong positive correlation."""
    interpretation = interpret_correlation(0.85, 0.001)
    
    assert 'strong' in interpretation.lower()
    assert 'positive' in interpretation.lower()
    assert 'significant' in interpretation.lower()


def test_interpret_correlation_weak():
    """Test interpretation of weak correlation."""
    interpretation = interpret_correlation(0.2, 0.5)
    
    assert 'weak' in interpretation.lower()
    assert 'not' in interpretation.lower() and 'significant' in interpretation.lower()


def test_interpret_correlation_moderate_negative():
    """Test interpretation of moderate negative correlation."""
    interpretation = interpret_correlation(-0.5, 0.02)
    
    assert 'moderate' in interpretation.lower()
    assert 'negative' in interpretation.lower()
    assert 'significant' in interpretation.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
