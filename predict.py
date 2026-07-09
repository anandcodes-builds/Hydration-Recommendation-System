import pandas as pd
import joblib
import os
import logging
from sklearn.exceptions import NotFittedError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for file paths
MODEL_PATH = 'model.pkl'
PREPROCESSOR_PATH = 'preprocessor.pkl'

def load_model_and_preprocessor():
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
            raise FileNotFoundError("Model or preprocessor file not found.")
        model = joblib.load(MODEL_PATH)
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        print("[INFO] Model and preprocessor loaded successfully.")
        return model, preprocessor
    except FileNotFoundError as fnf_error:
        print(f"[ERROR] {fnf_error}")
    except Exception as e:
        print(f"[ERROR] Unexpected error while loading model or preprocessor: {e}")
    return None, None

def get_user_input():
    try:
        print("\n Please enter your details for a hydration recommendation:\n")
        age = int(input("Age (e.g. 25): "))
        gender = input("Gender (Male/Female/Other): ").capitalize()
        weight = float(input("Weight in kg (e.g. 70.5): "))
        activity = input("Activity Level (Low/Moderate/High): ").capitalize()
        temperature = float(input("Temperature in °C (e.g. 30): "))
        special_needs = input("Special Needs (None/Athlete/Pregnancy/Kidney Condition/High Altitude): ").title()

        return {
            'Age': age,
            'Gender': gender,
            'Weight (kg)': weight,
            'Activity Level': activity,
            'Temperature (°C)': temperature,
            'Special Needs': special_needs
        }
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}")
        return None

def preprocess_input(input_data, preprocessor):
    try:
        required_columns = ['Age', 'Gender', 'Weight (kg)', 'Activity Level', 'Temperature (°C)', 'Special Needs']
        if not all(col in input_data for col in required_columns):
            raise ValueError(f"Missing input fields. Expected: {', '.join(required_columns)}")

        input_df = pd.DataFrame([input_data])
        input_df.columns = input_df.columns.str.replace(r'Temperature.*', 'Temperature (°C)', regex=True)

        column_mapping = {
            'Weight': 'Weight (kg)',
            'Activity_Level': 'Activity Level',
            'Special_Needs': 'Special Needs'
        }
        input_df.rename(columns=column_mapping, inplace=True)

        if 'Temperature (°C)' in input_df.columns:
            input_df['Temperature (°C)'] = pd.to_numeric(input_df['Temperature (°C)'], errors='coerce')

        if input_df.isnull().any().any():
            raise ValueError("Input contains missing or invalid values.")

        if hasattr(preprocessor, 'feature_names_in_'):
            expected_columns = preprocessor.feature_names_in_
            input_df = input_df.reindex(columns=expected_columns, fill_value=0)

        processed_data = preprocessor.transform(input_df)
        logging.info("Data preprocessing completed successfully.")
        return processed_data
    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        return None

def predict_water_intake(input_data):
    model, preprocessor = load_model_and_preprocessor()
    if model is None or preprocessor is None:
        return "Error: Model or preprocessor missing."

    processed_data = preprocess_input(input_data, preprocessor)
    if processed_data is None:
        return "Error: Preprocessing failed."

    try:
        prediction = model.predict(processed_data)
        return round(prediction[0], 2)
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return "Error: Prediction failed."

# -------- Main CLI --------
if __name__ == "__main__":
    user_input = get_user_input()
    if user_input:
        result = predict_water_intake(user_input)
        print(f"\n Recommended Water Intake: {result} liters\n")
