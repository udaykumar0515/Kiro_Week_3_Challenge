"""
Test suite for weather fetcher module.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from app.weather_fetcher import WeatherFetcher


@pytest.fixture
def fetcher():
    """Create a weather fetcher instance for testing."""
    return WeatherFetcher(cache_expiry_hours=1)


@pytest.fixture
def sample_weather_response():
    """Sample weather API response."""
    return {
        "latitude": 51.5,
        "longitude": -0.12,
        "hourly": {
            "time": [
                "2024-01-01T00:00",
                "2024-01-01T01:00",
                "2024-01-01T02:00"
            ],
            "temperature_2m": [10.5, 10.2, 9.8],
            "precipitation": [0.0, 0.1, 0.2],
            "cloudcover": [50, 60, 70],
            "windspeed_10m": [15.2, 16.1, 14.8]
        }
    }


def test_fetcher_initialization(fetcher):
    """Test that fetcher initializes correctly."""
    assert fetcher.cache_expiry_hours == 1
    assert fetcher.CACHE_DIR.exists()


def test_cache_path_generation(fetcher):
    """Test cache file path generation."""
    path = fetcher._get_cache_path(51.5, -0.12, "2024-01-01", "2024-01-31")
    
    assert path.parent == fetcher.CACHE_DIR
    assert "weather_" in path.name
    assert path.suffix == ".json"
    assert "51.5" in path.name
    assert "-0.12" in path.name


def test_cache_validation(fetcher, tmp_path):
    """Test cache expiry validation."""
    # Override cache dir for testing
    fetcher.CACHE_DIR = tmp_path
    
    # Create a fresh cache file
    cache_file = tmp_path / "test_cache.json"
    cache_file.write_text('{"test": "data"}')
    
    # Should be valid (just created)
    assert fetcher._is_cache_valid(cache_file) is True
    
    # Non-existent file should be invalid
    assert fetcher._is_cache_valid(tmp_path / "nonexistent.json") is False


def test_clear_cache(fetcher, tmp_path):
    """Test cache clearing functionality."""
    # Override cache dir
    fetcher.CACHE_DIR = tmp_path
    
    # Create some cache files
    (tmp_path / "weather_test1.json").write_text('{}')
    (tmp_path / "weather_test2.json").write_text('{}')
    (tmp_path / "other_file.txt").write_text('test')
    
    # Clear cache
    fetcher.clear_cache()
    
    # Weather caches should be gone
    assert not (tmp_path / "weather_test1.json").exists()
    assert not (tmp_path / "weather_test2.json").exists()
    
    # Other files should remain
    assert (tmp_path / "other_file.txt").exists()


def test_fetch_with_mock_response(fetcher, sample_weather_response, tmp_path, mocker):
    """Test fetching weather data with mocked API response."""
    # Override cache dir
    fetcher.CACHE_DIR = tmp_path
    
    # Mock the requests.get call
    mock_response = mocker.Mock()
    mock_response.json.return_value = sample_weather_response
    mock_response.raise_for_status = mocker.Mock()
    
    mocker.patch('requests.get', return_value=mock_response)
    
    # Fetch data
    data = fetcher.fetch_weather_data(
        latitude=51.5,
        longitude=-0.12,
        start_date="2024-01-01",
        end_date="2024-01-03"
    )
    
    # Verify data
    assert data is not None
    assert 'hourly' in data
    assert len(data['hourly']['time']) == 3
    assert data['hourly']['temperature_2m'][0] == 10.5
    
    # Verify cache was created
    cache_files = list(tmp_path.glob("weather_*.json"))
    assert len(cache_files) == 1


def test_fetch_uses_cache(fetcher, sample_weather_response, tmp_path):
    """Test that cached data is used when available."""
    # Override cache dir
    fetcher.CACHE_DIR = tmp_path
    
    # Create a cache file
    cache_path = fetcher._get_cache_path(51.5, -0.12, "2024-01-01", "2024-01-03")
    with open(cache_path, 'w') as f:
        json.dump(sample_weather_response, f)
    
    # Fetch data (should use cache, no API call)
    data = fetcher.fetch_weather_data(
        latitude=51.5,
        longitude=-0.12,
        start_date="2024-01-01",
        end_date="2024-01-03",
        use_cache=True
    )
    
    # Verify we got cached data
    assert data == sample_weather_response


def test_fetch_error_handling(fetcher, mocker):
    """Test error handling when API request fails."""
    # Mock a failed request
    mocker.patch('requests.get', side_effect=Exception("API Error"))
    
    # Fetch should return None on error
    data = fetcher.fetch_weather_data(
        latitude=51.5,
        longitude=-0.12,
        start_date="2024-01-01",
        end_date="2024-01-03"
    )
    
    assert data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
