"""
Weather data fetcher using Open-Meteo API.
Includes caching to avoid excessive API calls.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional


class WeatherFetcher:
    """Fetch historical weather data from Open-Meteo API with caching."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_DIR = Path("data/cache")
    
    def __init__(self, cache_expiry_hours: int = 24):
        """
        Initialize weather fetcher.
        
        Args:
            cache_expiry_hours: Hours before cache expires (default: 24)
        """
        self.cache_expiry_hours = cache_expiry_hours
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, latitude: float, longitude: float, start_date: str, end_date: str) -> Path:
        """Generate cache file path based on request parameters."""
        cache_key = f"{latitude}_{longitude}_{start_date}_{end_date}"
        return self.CACHE_DIR / f"weather_{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is not expired."""
        if not cache_path.exists():
            return False
        
        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < timedelta(hours=self.cache_expiry_hours)
    
    def fetch_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Fetch weather data for a location and date range.
        
        Args:
            latitude: Latitude of location
            longitude: Longitude of location
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary with weather data or None on error
        """
        cache_path = self._get_cache_path(latitude, longitude, start_date, end_date)
        
        # Try to use cache first
        if use_cache and self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    print(f"✓ Loaded weather data from cache: {cache_path.name}")
                    return data
            except Exception as e:
                print(f"⚠ Cache read error: {e}")
        
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
            
            print(f"→ Fetching weather data from Open-Meteo API...")
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Save to cache
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Weather data fetched and cached successfully")
            return data
            
        except requests.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return None
    
    def clear_cache(self):
        """Remove all cached weather files."""
        count = 0
        for cache_file in self.CACHE_DIR.glob("weather_*.json"):
            cache_file.unlink()
            count += 1
        print(f"✓ Cleared {count} weather cache files")


if __name__ == "__main__":
    # Test the fetcher
    fetcher = WeatherFetcher()
    
    # Example: London weather for last 30 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    data = fetcher.fetch_weather_data(
        latitude=51.5074,
        longitude=-0.1278,
        start_date=start_date,
        end_date=end_date
    )
    
    if data:
        print(f"\nSample data keys: {list(data.keys())}")
        if 'hourly' in data:
            print(f"Hourly data points: {len(data['hourly']['time'])}")
