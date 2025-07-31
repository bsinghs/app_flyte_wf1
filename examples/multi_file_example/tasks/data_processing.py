from flytekit import task, Resources
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import logging

@task(requests=Resources(cpu="300m", mem="300Mi"), limits=Resources(cpu="500m", mem="500Mi"))
def load_data(data_path: str) -> pd.DataFrame:
    """Load data from CSV file"""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading data from: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records")
    return df

@task(requests=Resources(cpu="200m", mem="200Mi"), limits=Resources(cpu="400m", mem="400Mi"))
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess data"""
    logger = logging.getLogger(__name__)
    
    # Remove rows with missing values
    df_clean = df.dropna()
    logger.info(f"After cleaning: {len(df_clean)} records")
    
    return df_clean

@task(requests=Resources(cpu="200m", mem="300Mi"), limits=Resources(cpu="400m", mem="500Mi"))
def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical features"""
    logger = logging.getLogger(__name__)
    
    # Apply encoding
    df_encoded = pd.get_dummies(df)
    logger.info(f"Encoded features: {df_encoded.columns.tolist()}")
    
    return df_encoded
