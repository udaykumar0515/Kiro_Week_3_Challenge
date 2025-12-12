"""
Google Trends data fetcher using pytrends library.
Includes caching and rate limiting to be respectful.
"""

import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from pytrends.request import TrendReq


class TrendsFetcher:
    """Fetch Google Trends data with caching and rate limiting."""
    
    CACHE_DIR = Path("data/cache")
    SAMPLE_DIR = Path("data/sample")
    
    def __init__(self, cache_expiry_days: int = 7):
        """
        Initialize trends fetcher.
        
        Args:
            cache_expiry_days: Days before cache expires (default: 7)
        """
        self.cache_expiry_days = cache_expiry_days
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.pytrends = None
    
    def _init_pytrends(self):
        """Initialize pytrends object with retry logic."""
        if self.pytrends is None:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
                time.sleep(1)  # Be respectful with API
            except Exception as e:
                print(f"⚠ Error initializing pytrends: {e}")
                raise
    
    def _get_cache_path(self, keyword: str, start_date: str, end_date: str, geo: str) -> Path:
        """Generate cache file path based on request parameters."""
        cache_key = f"{keyword}_{geo}_{start_date}_{end_date}".replace(" ", "_")
        return self.CACHE_DIR / f"trends_{cache_key}.csv"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is not expired."""
        if not cache_path.exists():
            return False
        
        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < timedelta(days=self.cache_expiry_days)
    
    def fetch_trends_data(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        geo: str = '',
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Fetch Google Trends data for a keyword and date range.
        
        Args:
            keyword: Search term to analyze
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            geo: Geographic location (empty string for worldwide, 'US' for USA, etc.)
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with trends data or None on error
        """
        cache_path = self._get_cache_path(keyword, start_date, end_date, geo or 'worldwide')
        
        # Try to use cache first
        if use_cache and self._is_cache_valid(cache_path):
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                print(f"✓ Loaded trends data from cache: {cache_path.name}")
                return df
            except Exception as e:
                print(f"⚠ Cache read error: {e}")
        
        # Fetch from Google Trends
        try:
            self._init_pytrends()
            
            # Build timeframe string
            timeframe = f"{start_date} {end_date}"
            
            print(f"→ Fetching Google Trends data for '{keyword}'...")
            print(f"  Timeframe: {timeframe}, Geo: {geo or 'worldwide'}")
            
            # Build payload
            self.pytrends.build_payload(
                kw_list=[keyword],
                timeframe=timeframe,
                geo=geo
            )
            
            # Get interest over time
            df = self.pytrends.interest_over_time()
            
            if df.empty:
                print(f"⚠ No trends data available for '{keyword}'")
                return None
            
            # Drop 'isPartial' column if it exists
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
            
            # Save to cache
            df.to_csv(cache_path)
            print(f"✓ Trends data fetched and cached successfully")
            
            # Be respectful - add delay
            time.sleep(2)
            
            return df
            
        except Exception as e:
            print(f"✗ Error fetching trends data: {e}")
            print(f"  Note: Google Trends may rate-limit. Trying sample data fallback...")
            
            # Try to load from sample directory as fallback
            sample_path = self.SAMPLE_DIR / f"trends_{keyword}_{geo or 'worldwide'}_{start_date}_{end_date}.csv"
            if sample_path.exists():
                try:
                    df = pd.read_csv(sample_path, index_col=0, parse_dates=True)
                    print(f"✓ Loaded sample data from: {sample_path.name}")
                    return df
                except Exception as fallback_error:
                    print(f"⚠ Failed to load sample data: {fallback_error}")
            else:
                print(f"⚠ No sample data found at: {sample_path}")
            
            return None
    
    def clear_cache(self):
        """Remove all cached trends files."""
        count = 0
        for cache_file in self.CACHE_DIR.glob("trends_*.csv"):
            cache_file.unlink()
            count += 1
        print(f"✓ Cleared {count} trends cache files")


if __name__ == "__main__":
    # Test the fetcher
    fetcher = TrendsFetcher()
    
    # Example: 'umbrella' trends for last 90 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    df = fetcher.fetch_trends_data(
        keyword='umbrella',
        start_date=start_date,
        end_date=end_date,
        geo=''  # Worldwide
    )
    
    if df is not None:
        print(f"\nSample data:")
        print(df.head())
        print(f"\nData shape: {df.shape}")
