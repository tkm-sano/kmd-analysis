import pandas as pd

def safe_to_parquet(df: pd.DataFrame, path):
    try:
        df.to_parquet(path, index=False)
        return str(path)
    except Exception:
        csv_path = str(path).replace(".parquet", ".csv")
        df.to_csv(csv_path, index=False)
        return csv_path
