import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

def run_automated_etl(df: pd.DataFrame):
    """
    Automatically Extracts, Transforms, and prepares an uploaded DataFrame 
    for downstream Machine Learning tasks.
    """
    # Create a deep copy to preserve the original raw data if needed
    cleaned_df = df.copy()
    
    # ----------------------------------------------------
    # STEP 1: Handle Missing Values (Imputation)
    # ----------------------------------------------------
    for col in cleaned_df.columns:
        if cleaned_df[col].isnull().sum() > 0:
            # If the column is numeric, fill missing blocks with the median
            if np.issubdtype(cleaned_df[col].dtype, np.number):
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            # If the column is text/categorical, fill with the most common value (mode)
            else:
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])
                
    # ----------------------------------------------------
    # STEP 2: Encode Categorical Text Columns to Numbers
    # ----------------------------------------------------
    # ML models only speak math. We must turn "Yes/No" or "Red/Blue" into 0s and 1s.
    label_encoders = {}
    for col in cleaned_df.columns:
        if not np.issubdtype(cleaned_df[col].dtype, np.number):
            le = LabelEncoder()
            # Convert column to string type to avoid mix-type classification issues
            cleaned_df[col] = le.fit_transform(cleaned_df[col].astype(str))
            label_encoders[col] = le
            
    # ----------------------------------------------------
    # STEP 3: Scale Numerical Features
    # ----------------------------------------------------
    # Standardize values so columns with huge ranges (like Salary) don't overpower smaller ones (like Age)
    numerical_cols = [col for col in cleaned_df.columns if np.issubdtype(cleaned_df[col].dtype, np.number)]
    
    if len(numerical_cols) > 0:
        scaler = StandardScaler()
        cleaned_df[numerical_cols] = scaler.fit_transform(cleaned_df[numerical_cols])
        
    return cleaned_df