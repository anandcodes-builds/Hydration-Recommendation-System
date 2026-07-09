import pandas as pd
import numpy as np

def preprocess_input(input_data, preprocessor):
    try:
        # Convert input data to DataFrame
        input_df = pd.DataFrame([input_data])

        # Fix column names for temperature using regex
        input_df.columns = input_df.columns.str.replace(r'Temperature.*', 'Temperature (°C)', regex=True)

        print("[INFO] Fixed Column Names:", input_df.columns)

        # Column Mapping to Resolve Name Mismatches
        column_mapping = {
            'Weight': 'Weight (kg)',
            'Activity_Level': 'Activity Level',
            'Special_Needs': 'Special Needs'
        }
        input_df.rename(columns=column_mapping, inplace=True)

        # Ensure temperature is a numeric value
        if 'Temperature (°C)' in input_df.columns:
            input_df['Temperature (°C)'] = pd.to_numeric(input_df['Temperature (°C)'], errors='coerce')

        # Align input columns with expected model columns
        if hasattr(preprocessor, 'feature_names_in_'):
            expected_columns = preprocessor.feature_names_in_
            missing_cols = set(expected_columns) - set(input_df.columns)
            extra_cols = set(input_df.columns) - set(expected_columns)

            if missing_cols:
                print(f"[WARNING] Missing columns: {missing_cols}")
            if extra_cols:
                print(f"[WARNING] Extra columns: {extra_cols}")

            # Reindex to align columns, filling missing ones with 0
            input_df = input_df.reindex(columns=expected_columns, fill_value=0)
            print("[INFO] Input data aligned with expected columns.")

        # Apply preprocessing using the preprocessor
        processed_data = preprocessor.transform(input_df)
        print("[INFO] Processed Data (After Encoding):", processed_data)
        return processed_data
    except Exception as e:
        print(f"[ERROR] Error during preprocessing: {e}")
        return None