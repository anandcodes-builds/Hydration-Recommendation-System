import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

def clean_data(data):
    try:
        # Remove any unnamed columns
        data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
        print("[INFO] Unnamed columns removed.")

        # Strip whitespace and fix column names
        data.columns = data.columns.str.strip()
        data.columns = data.columns.str.replace(r"\s+", " ", regex=True)
        data.columns = data.columns.str.replace(r"[^\x00-\x7F]+", " ", regex=True)
        
        data.rename(columns={
            'Temperature ( C)': 'Temperature (°C)'
        }, inplace=True, errors='ignore')
        
        # Remove units like '°C' or 'kg' and convert to numeric
        if 'Weight (kg)' in data.columns:
            data.loc[:, 'Weight (kg)'] = pd.to_numeric(data['Weight (kg)'].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce')

        if 'Temperature (°C)' in data.columns:
            data.loc[:, 'Temperature (°C)'] = pd.to_numeric(data['Temperature (°C)'].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce')

        # Convert categorical columns to string
        categorical_cols = ['Gender', 'Activity Level', 'Special Needs']
        for col in categorical_cols:
            if col in data.columns:
                data.loc[:, col] = data[col].astype(str).str.strip()

        # Fill missing values for numeric columns
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        data.loc[:, numeric_cols] = data[numeric_cols].fillna(data[numeric_cols].mean())

        print("[INFO] Missing numeric values filled with mean.")
        print("[INFO] Cleaned Columns:", data.columns)
        return data

    except Exception as e:
        print(f"[ERROR] Error during data cleaning: {e}")
        return None

def encode_data(data):
    try:
        categorical_features = ['Gender', 'Activity Level', 'Special Needs']
        numerical_features = ['Age', 'Weight (kg)', 'Temperature (°C)']

        # Ensure the target column is not included in preprocessing
        if 'Water_Intake' in data.columns:
            data = data.drop('Water_Intake', axis=1)
        
        # Validate columns
        missing_cols = [col for col in categorical_features + numerical_features if col not in data.columns]
        if missing_cols:
            raise ValueError(f"[ERROR] Missing columns from the dataset: {missing_cols}")
        
        # Handle missing values using SimpleImputer
        imputer = SimpleImputer(strategy='mean')
        data[numerical_features] = imputer.fit_transform(data[numerical_features])

        # Build a preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ]
        )

        # Fit the preprocessor
        preprocessor.fit(data)

        # Save the fitted preprocessor
        joblib.dump(preprocessor, 'preprocessor.pkl')
        print("[INFO] Preprocessor fitted and saved successfully.")
        return preprocessor.transform(data)

    except Exception as e:
        print(f"[ERROR] Error during encoding: {e}")
        return None

def train_model(file_path, model_path='model.pkl'):
    try:
        # Load data
        data = pd.read_csv(file_path, encoding='utf-8')
        print("[INFO] Data loaded successfully.")
        
        # Clean and preprocess data
        data = clean_data(data)
        if data is None:
            return
        
        print("[INFO] Final Cleaned Columns for Encoding:", data.columns)
        processed_data = encode_data(data)
        if processed_data is None:
            return

        # Extract target column
        target_column = [col for col in data.columns if col.lower() == 'water_intake']
        if not target_column:
            raise ValueError("[ERROR] 'Water_Intake' column not found.")
        
        X = processed_data
        y = data[target_column[0]]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        print("[INFO] Training model...")
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Evaluate model
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        print(f"[INFO] Mean Squared Error: {mse}")
        print(f"[INFO] Mean Absolute Error: {mae}")
        print(f"[INFO] R2 Score: {r2}")

        # Save model in the specified path
        if os.path.dirname(model_path):  # Only create directory if path is non-empty
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

        joblib.dump(model, model_path)
        print(f"[INFO] Model saved successfully at: {model_path}")

    except Exception as e:
        print(f"[ERROR] Error during training: {e}")

# Example usage
train_model('hydration_recommendation.csv')
