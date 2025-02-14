"""
An R / glimpse-like utility written in Python
"""

def glimpse(df):
    """
    Display DataFrame info similar to R's glimpse function.
    Shows the number of rows and columns, and a preview of each column's type and first few values.
    """
    # Display DataFrame shape
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print("\nColumn preview:")
    print("-" * 80)
    
    # Iterate through columns
    for col in df.columns:
        try:
            # Get first few values, handle missing values
            sample = df[col].iloc[:5].fillna("None").astype(str).tolist()
            # Truncate long strings for readability
            sample = [s[:50] + "..." if len(s) > 50 else s for s in sample]
            sample_str = ", ".join(sample)
        except Exception as e:
            sample_str = f"Error: {e}"
        
        # Print column details
        print(f"{col:<25} <{df[col].dtype}> {sample_str}")