import requests
import os
import json
import time
import pandas as pd
from typing import List, Dict, Optional, Union
from pathlib import Path

class OMDbDownloader:
    """
    A simple client for downloading movie data from the OMDb API
    """
    
    def __init__(self, api_key: str, cache_dir: str = "./omdb_cache"):
        """
        Initialize the OMDb downloader.
        
        Args:
            api_key: OMDb API key
            cache_dir: Directory to store cached responses
        """
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure request timeout and retry settings
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def fetch_by_id(self, imdb_id: str, force_refresh: bool = False) -> Dict:
        """
        Fetch movie data for a single IMDb ID.
        
        Args:
            imdb_id: IMDb ID (e.g., tt0133093)
            force_refresh: Whether to force a refresh from the API
            
        Returns:
            Dictionary containing the raw API response
        """
        cache_file = self.cache_dir / f"{imdb_id}.json"
        
        # Try to load from cache if not forcing refresh
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Cache file is corrupted, continue to API call
                pass
        
        # Prepare API request parameters
        params = {
            'i': imdb_id,
            'apikey': self.api_key,
            'plot': 'full',
            'r': 'json'
        }
        
        # Make API request with retries
        data = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()  # Raise exception for HTTP errors
                data = response.json()
                break
            except (requests.RequestException, json.JSONDecodeError) as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to fetch data for {imdb_id}: {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        
        return data
    
    def fetch_by_ids(self, imdb_ids: List[str], force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Fetch movie data for multiple IMDb IDs.
        
        Args:
            imdb_ids: List of IMDb IDs
            force_refresh: Whether to force a refresh from the API
            
        Returns:
            Dictionary mapping IMDb IDs to raw API responses
        """
        results = {}
        for imdb_id in imdb_ids:
            try:
                results[imdb_id] = self.fetch_by_id(imdb_id, force_refresh)
            except Exception as e:
                print(f"Error fetching {imdb_id}: {str(e)}")
                results[imdb_id] = {"Error": str(e), "Response": "False"}
        
        return results
    
    def search(self, title: str, year: Optional[int] = None, type_: Optional[str] = None) -> Dict:
        """
        Search for movies by title.
        
        Args:
            title: Movie title to search for
            year: Optional year of release
            type_: Optional type (movie, series, episode)
            
        Returns:
            Dictionary containing the raw API response
        """
        cache_key = f"search_{title}_{year}_{type_}"
        cache_file = self.cache_dir / f"{cache_key.replace(' ', '_')}.json"
        
        # Try to load from cache
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Cache file is corrupted, continue to API call
                pass
        
        # Prepare API request parameters
        params = {
            's': title,
            'apikey': self.api_key,
            'r': 'json'
        }
        
        if year is not None:
            params['y'] = str(year)
        
        if type_ is not None:
            params['type'] = type_
        
        # Make API request with retries
        data = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                break
            except (requests.RequestException, json.JSONDecodeError) as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to search for '{title}': {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))
        
        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        
        return data

class OMDbConverter:
    """
    Convert OMDb API responses to pandas DataFrames
    """
    
    @staticmethod
    def response_to_dataframe(response: Dict) -> pd.DataFrame:
        """
        Convert a single OMDb API response to a DataFrame row.
        
        Args:
            response: OMDb API response
            
        Returns:
            DataFrame with one row
        """
        # Handle error responses
        if response.get('Response') == 'False':
            return pd.DataFrame({
                'imdb_id': [response.get('imdbID', 'N/A')],
                'error': [response.get('Error', 'Unknown error')]
            })
        
        # Extract all fields
        data = {k.lower(): [v] for k, v in response.items()}
        
        # Convert 'ratings' to separate columns
        if 'ratings' in data:
            ratings = data['ratings'][0]
            if isinstance(ratings, list):
                for rating in ratings:
                    source = rating.get('Source', '').replace(' ', '_').lower()
                    value = rating.get('Value', '')
                    data[f'rating_{source}'] = [value]
            
            # Remove the original ratings list
            del data['ratings']
        
        return pd.DataFrame(data)
    
    @staticmethod
    def responses_to_dataframe(responses: Dict[str, Dict]) -> pd.DataFrame:
        """
        Convert multiple OMDb API responses to a DataFrame.
        
        Args:
            responses: Dictionary mapping IMDb IDs to OMDb API responses
            
        Returns:
            DataFrame with one row per movie
        """
        # Convert each response to a DataFrame and concatenate
        dfs = []
        for imdb_id, response in responses.items():
            # Add imdb_id if not present in response
            if 'imdbID' not in response:
                response['imdbID'] = imdb_id
                
            dfs.append(OMDbConverter.response_to_dataframe(response))
        
        if not dfs:
            return pd.DataFrame()
            
        return pd.concat(dfs, ignore_index=True)
    
    @staticmethod
    def search_to_dataframe(search_response: Dict) -> pd.DataFrame:
        """
        Convert an OMDb API search response to a DataFrame.
        
        Args:
            search_response: OMDb API search response
            
        Returns:
            DataFrame with search results
        """
        # Handle error responses
        if search_response.get('Response') == 'False':
            return pd.DataFrame()
        
        # Extract search results
        search_results = search_response.get('Search', [])
        if not search_results:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(search_results)
        
        # Normalize column names
        df.columns = [c.lower() for c in df.columns]
        
        return df
        
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize a DataFrame created from OMDb API responses.
        
        Args:
            df: DataFrame created from OMDb API responses
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Convert runtime to minutes (numeric)
        if 'runtime' in df.columns:
            df['runtime_minutes'] = df['runtime'].str.extract(r'(\d+)').astype(float)
        
        # Convert ratings to numeric
        for col in df.columns:
            if col.startswith('rating_') or col == 'imdbrating':
                # Handle ratings that might have formats like "8.5/10"
                df[col] = pd.to_numeric(df[col].str.replace(r'/.*$', '', regex=True), errors='coerce')
        
        # Convert votes to numeric - handle commas properly
        if 'imdbvotes' in df.columns:
            df['imdbvotes_numeric'] = pd.to_numeric(df['imdbvotes'].str.replace(',', ''), errors='coerce')
        
        # Convert box office to numeric - handle currency symbols and commas
        if 'boxoffice' in df.columns:
            # First extract the numeric part with commas removed
            df['boxoffice_value'] = df['boxoffice'].str.replace(r'[^\d.]', '', regex=True)
            # Then convert to float
            df['boxoffice_value'] = pd.to_numeric(df['boxoffice_value'], errors='coerce')
        
        # Create genre list column
        if 'genre' in df.columns:
            df['genre_list'] = df['genre'].str.split(',').apply(
                lambda x: [g.strip() for g in x] if isinstance(x, list) else []
            )
        
        # Create actors list column
        if 'actors' in df.columns:
            df['actor_list'] = df['actors'].str.split(',').apply(
                lambda x: [a.strip() for a in x] if isinstance(x, list) else []
            )
        
        # Create director list column
        if 'director' in df.columns:
            df['director_list'] = df['director'].str.split(',').apply(
                lambda x: [d.strip() for d in x] if isinstance(x, list) else []
            )
        
        return df
