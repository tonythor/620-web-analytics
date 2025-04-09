import pandas as pd

class Glimpse:
    def __init__(self, df, sample_size=5, random=False):
        """
        Display DataFrame info similar to R's glimpse function.
        
        Parameters:
        - df: pandas DataFrame
        - sample_size: Number of rows to display for each column
        - random: Whether to display a random sample or the first few rows
        """
        # Basic DataFrame info
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")
        print("\nColumn preview:")
        print("-" * 80)
        
        # For each column, show type and sample values
        for col in df.columns:
            try:
                # Get a random or sequential sample
                if random:
                    sample = df[col].sample(n=min(sample_size, len(df)), random_state=42).tolist()
                else:
                    sample = df[col].head(sample_size).tolist()
                
                # Truncate long strings
                sample = [str(x)[:50] + '...' if isinstance(x, str) and len(str(x)) > 50 else str(x) for x in sample]
                sample_str = ', '.join(sample)
            except Exception as e:
                sample_str = f"Error getting samples: {e}"
            
            # Print column info
            print(f"{col:<20} <{df[col].dtype}> {sample_str}")