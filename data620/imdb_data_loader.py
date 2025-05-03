import os
import pandas as pd
import gzip
import shutil
import requests
from pathlib import Path
import time
from typing import Dict, List, Optional, Union, Tuple

class IMDbDataLoader:
    """
    A class to handle loading, filtering, and accessing IMDb datasets.
    
    This class handles the complete workflow for IMDb data:
    1. Downloading raw data files if needed
    2. Extracting the files if needed
    3. Filtering the data to recent/relevant entries
    4. Persisting the filtered dataframes
    5. Providing easy access to the filtered dataframes
    
    Usage:
        imdb = IMDbDataLoader()
        imdb.load()
        
        # Access dataframes directly as properties
        movies_df = imdb.titles
        actors_df = imdb.names
    """
    
    def __init__(
        self, 
        base_url: str = "https://datasets.imdbws.com/",
        raw_data_dir: str = "./nogit_imdb_data/",
        filtered_data_dir: str = "./nogit_imdb_filtered/",
        min_year: int = 2015,
        min_votes: int = 5000,
        min_rating: float = 6.0
    ):
        """
        Initialize the IMDb data loader.
        
        Args:
            base_url: URL for the IMDb data files
            raw_data_dir: Directory to store the raw data files
            filtered_data_dir: Directory to store the filtered dataframes
            min_year: Minimum year for filtering movies (inclusive)
            min_votes: Minimum number of votes for filtering movies
            min_rating: Minimum rating for filtering movies
        """
        self.base_url = base_url
        self.raw_data_dir = Path(raw_data_dir)
        self.filtered_data_dir = Path(filtered_data_dir)
        self.min_year = min_year
        self.min_votes = min_votes
        self.min_rating = min_rating
        
        # Dictionary mapping dataset names to file names
        self.dataset_files = {
            "titles": "title.basics.tsv.gz",
            "ratings": "title.ratings.tsv.gz",
            "principals": "title.principals.tsv.gz",
            "names": "name.basics.tsv.gz",
            "episodes": "title.episode.tsv.gz",
            "akas": "title.akas.tsv.gz",
            "crew": "title.crew.tsv.gz"
        }
        
        # Initialize dataframe properties to None
        self._titles = None
        self._ratings = None
        self._principals = None
        self._names = None
        self._episodes = None
        self._akas = None
        self._crew = None
        
        # Flag to track if data has been loaded
        self._loaded = False
    
    def load(self, force_refresh: bool = False) -> bool:
        """
        Load all IMDb datasets, handling download, extraction, 
        filtering, and persistence as needed.
        
        Args:
            force_refresh: If True, redownload and reprocess all data
            
        Returns:
            True if loading was successful, False otherwise
        """
        print("Loading IMDb data...")
        
        # Check if filtered data already exists and we're not forcing a refresh
        if not force_refresh and self._check_filtered_data_exists():
            print("Filtered data found. Loading from filtered files.")
            self._load_filtered_data()
            self._loaded = True
            return True
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(exist_ok=True, parents=True)
        self.filtered_data_dir.mkdir(exist_ok=True, parents=True)
        
        # Download raw data if needed
        for name, file_name in self.dataset_files.items():
            local_path = self.raw_data_dir / file_name
            
            if force_refresh or not local_path.exists():
                print(f"Downloading {file_name}...")
                success = self._download_file(file_name)
                if not success:
                    print(f"Failed to download {file_name}")
                    return False
            else:
                print(f"File {file_name} already exists")
        
        # Load, filter and persist data
        try:
            self._process_data()
            self._loaded = True
            return True
        except Exception as e:
            print(f"Error processing data: {e}")
            return False
    
    def _check_filtered_data_exists(self) -> bool:
        """Check if filtered data files exist"""
        for name in self.dataset_files.keys():
            filtered_path = self.filtered_data_dir / f"{name}_filtered.parquet"
            if not filtered_path.exists():
                return False
        return True
    
    def _load_filtered_data(self) -> None:
        """Load data from filtered parquet files"""
        for name in self.dataset_files.keys():
            filtered_path = self.filtered_data_dir / f"{name}_filtered.parquet"
            if filtered_path.exists():
                print(f"Loading {name} from filtered file...")
                setattr(self, f"_{name}", pd.read_parquet(filtered_path))
    
    def _download_file(self, file_name: str) -> bool:
        """Download a file from IMDb dataset"""
        file_url = self.base_url + file_name
        local_path = self.raw_data_dir / file_name
        
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            print(f"Download complete: {file_name}")
            return True
        except Exception as e:
            print(f"Error downloading {file_name}: {e}")
            return False
    
    def _process_data(self) -> None:
        """Load, filter, and persist all datasets"""
        # Load and filter titles and ratings first
        self._load_and_filter_titles_ratings()
        
        # Process other datasets based on filtered titles
        for name, file_name in self.dataset_files.items():
            if name in ['titles', 'ratings']:
                continue  # Already processed
                
            print(f"Processing {name}...")
            
            # Load and filter the dataset
            df = self._load_and_filter_dataset(name, file_name)
            
            # Store in memory
            setattr(self, f"_{name}", df)
            
            # Save filtered data
            filtered_path = self.filtered_data_dir / f"{name}_filtered.parquet"
            df.to_parquet(filtered_path, index=False)
            print(f"Saved filtered {name} dataset")
    
    def _load_and_filter_titles_ratings(self) -> None:
        """Load and filter titles and ratings datasets"""
        # Load titles
        titles_path = self.raw_data_dir / self.dataset_files["titles"]
        print("Loading titles dataset...")
        titles_df = pd.read_csv(titles_path, sep='\t', low_memory=False)
        
        # Basic filtering of titles
        print("Filtering titles...")
        titles_df = titles_df[titles_df['titleType'] == 'movie']  # Only movies
        titles_df['startYear'] = pd.to_numeric(titles_df['startYear'], errors='coerce')
        titles_df = titles_df[titles_df['startYear'] >= self.min_year]  # Recent movies
        
        # Load ratings
        ratings_path = self.raw_data_dir / self.dataset_files["ratings"]
        print("Loading ratings dataset...")
        ratings_df = pd.read_csv(ratings_path, sep='\t', low_memory=False)
        
        # Merge and filter by ratings
        print("Merging titles with ratings...")
        merged_df = pd.merge(titles_df, ratings_df, on='tconst', how='inner')
        
        # Apply rating and votes filters
        filtered_df = merged_df[
            (merged_df['averageRating'] >= self.min_rating) & 
            (merged_df['numVotes'] >= self.min_votes)
        ]
        
        # Extract title and rating dataframes from filtered data
        self._titles = filtered_df[titles_df.columns]
        self._ratings = filtered_df[['tconst', 'averageRating', 'numVotes']]
        
        # Create list of title IDs to filter other datasets
        self.filtered_title_ids = set(self._titles['tconst'])
        
        # Save filtered dataframes
        titles_path = self.filtered_data_dir / "titles_filtered.parquet"
        ratings_path = self.filtered_data_dir / "ratings_filtered.parquet"
        
        self._titles.to_parquet(titles_path, index=False)
        self._ratings.to_parquet(ratings_path, index=False)
        
        print(f"Saved filtered titles and ratings datasets")
        print(f"Filtered dataset contains {len(self._titles):,} movies")
    
    def _load_and_filter_dataset(self, name: str, file_name: str) -> pd.DataFrame:
        """Load and filter a dataset based on filtered title IDs"""
        file_path = self.raw_data_dir / file_name
        
        # Load the dataset
        df = pd.read_csv(file_path, sep='\t', low_memory=False)
        
        # Filter based on title IDs if the dataset contains title references
        if 'tconst' in df.columns:
            filtered_df = df[df['tconst'].isin(self.filtered_title_ids)]
            print(f"Filtered {name} from {len(df):,} to {len(filtered_df):,} rows")
            return filtered_df
        else:
            # For datasets like names, filter based on usage in principals
            if name == 'names' and self._principals is not None:
                person_ids = set(self._principals['nconst'])
                filtered_df = df[df['nconst'].isin(person_ids)]
                print(f"Filtered {name} from {len(df):,} to {len(filtered_df):,} rows")
                return filtered_df
            
            # Otherwise, return the original dataset
            print(f"No filtering applied to {name} dataset")
            return df
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the loaded data"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return {}
        
        stats = {}
        
        # Titles stats
        if self._titles is not None:
            stats['titles_count'] = len(self._titles)
            
            # Count by year
            year_counts = self._titles['startYear'].value_counts().sort_index()
            stats['year_counts'] = year_counts.to_dict()
            
            # Count by genre
            if 'genres' in self._titles.columns:
                self._titles['genre_list'] = self._titles['genres'].str.split(',')
                exploded = self._titles.explode('genre_list')
                genre_counts = exploded['genre_list'].value_counts()
                stats['genre_counts'] = genre_counts.to_dict()
        
        # Ratings stats
        if self._ratings is not None:
            stats['avg_rating'] = self._ratings['averageRating'].mean()
            stats['median_rating'] = self._ratings['averageRating'].median()
            stats['avg_votes'] = self._ratings['numVotes'].mean()
            stats['median_votes'] = self._ratings['numVotes'].median()
        
        # Principals stats
        if self._principals is not None:
            stats['principals_count'] = len(self._principals)
            
            # Count by category
            if 'category' in self._principals.columns:
                category_counts = self._principals['category'].value_counts()
                stats['category_counts'] = category_counts.to_dict()
        
        # Names stats
        if self._names is not None:
            stats['names_count'] = len(self._names)
        
        return stats
    
    def print_summary(self) -> None:
        """Print a summary of the loaded data"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return
        
        stats = self.get_summary_stats()
        
        print("\n===== IMDb Dataset Summary =====\n")
        
        if 'titles_count' in stats:
            print(f"Total filtered movies: {stats['titles_count']:,}")
        
        if 'year_counts' in stats:
            print("\nMovies by year:")
            for year, count in sorted(stats['year_counts'].items()):
                print(f"  {year}: {count:,}")
        
        if 'genre_counts' in stats:
            print("\nTop genres:")
            sorted_genres = sorted(stats['genre_counts'].items(), key=lambda x: x[1], reverse=True)
            for genre, count in sorted_genres[:15]:
                if genre != '\\N' and not pd.isna(genre):
                    print(f"  {genre}: {count:,}")
        
        if 'avg_rating' in stats:
            print(f"\nAverage rating: {stats['avg_rating']:.2f}")
            print(f"Median rating: {stats['median_rating']:.2f}")
            print(f"Average votes: {stats['avg_votes']:,.0f}")
            print(f"Median votes: {stats['median_votes']:,.0f}")
        
        if 'category_counts' in stats:
            print("\nTop cast/crew categories:")
            sorted_categories = sorted(stats['category_counts'].items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:10]:
                print(f"  {category}: {count:,}")
        
        if 'names_count' in stats:
            print(f"\nTotal people (actors, directors, etc.): {stats['names_count']:,}")
    
    # Properties to access the dataframes
    @property
    def titles(self) -> pd.DataFrame:
        """Get the titles dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._titles
    
    @property
    def ratings(self) -> pd.DataFrame:
        """Get the ratings dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._ratings
    
    @property
    def principals(self) -> pd.DataFrame:
        """Get the principals dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._principals
    
    @property
    def names(self) -> pd.DataFrame:
        """Get the names dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._names
    
    @property
    def episodes(self) -> pd.DataFrame:
        """Get the episodes dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._episodes
    
    @property
    def akas(self) -> pd.DataFrame:
        """Get the akas dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._akas
    
    @property
    def crew(self) -> pd.DataFrame:
        """Get the crew dataframe"""
        if not self._loaded:
            print("Data not loaded. Call load() first.")
            return pd.DataFrame()
        return self._crew