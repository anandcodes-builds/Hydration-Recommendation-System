import streamlit as st
from joblib import load
import numpy as np
import pandas as pd
import requests
import datetime
import plotly.express as px
import bcrypt
import smtplib
from email.mime.text import MIMEText
import sqlite3
from datetime import datetime
import re
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Set up page config
st.set_page_config(page_title="Hydration Recommender", layout="centered")

# Title of the app
st.title("Stay Hydrated! 💧")

# st.write("Secrets email:", st.secrets["email"]["address"])

# Custom CSS for styling
st.markdown("""
<style>
/* --- Input Field Styling (Text, Password) - Remove Border --- */
.stTextInput > div > div > input,
.stPasswordInput > div > div > input {
 border: none !important; /* Remove default border */
 border-radius: 0.5rem !important;
 padding: 0.5rem !important;
 color: white !important;
 background: rgba(255, 255, 255, 0.05) !important;
 backdrop-filter: blur(6px) !important;
}

/* Hover state for Text and Password Inputs - No Border */
.stTextInput > div > div > input:hover,
.stPasswordInput > div > div > input:hover {
 border: none !important; /* Ensure no border on hover */
}

/* --- Number Input Styling - Remove Border from Container --- */
.stNumberInput > div {
 border-radius: 0.5rem !important;
 background: rgba(255, 255, 255, 0.05) !important;
 backdrop-filter: blur(6px);
 border: none !important; /* Remove border from the number input container */
}

/* Minus Button - Red */
.stNumberInput button:first-child {
 background-color: red !important;
 color: white !important;
 border: none !important;
 border-radius: 0.25rem !important;
}
.stNumberInput button:first-child:hover {
 background-color: #cc0000 !important;
}

/* Plus Button - Green */
.stNumberInput button:last-child {
 background-color: #28a745 !important;
 color: white !important;
 border: none !important;
 border-radius: 0.25rem !important;
}
.stNumberInput button:last-child:hover {
 background-color: #218838 !important;
}

/* --- Focus state for all Inputs (No Border, Keep Box Shadow) --- */
.stTextInput > div > div > input:focus,
.stPasswordInput > div > div > input:focus,
.stNumberInput input:focus {
 border: none !important; /* Remove border on focus */
 border-color: transparent !important; /* Ensure border color is transparent */
 box-shadow: 0 0 5px rgba(0, 123, 255, 0.4) !important; /* Keep the blue box shadow */
 outline: none !important; /* Remove default outline */
}

/* ✅ Style for invalid inputs (No Border, Keep Box Shadow) */
input[aria-invalid="true"],
.stTextInput input[aria-invalid="true"],
.stPasswordInput input[aria-invalid="true"],
.stNumberInput input[aria-invalid="true"] {
 border: none !important; /* Remove border for invalid state */
 border-color: transparent !important; /* Ensure border color is transparent */
 box-shadow: 0 0 5px rgba(0, 123, 255, 0.4) !important; /* Keep the blue box shadow as indicator */
 outline: none !important;
}


/* --- Main Button Styling (Blue Theme) --- */
.stButton > button {
 background-color: rgba(0, 123, 255, 0.8) !important;
 color: white !important;
 border: none !important;
 border-radius: 0.5rem !important;
 padding: 0.6rem 1.2rem !important;
 transition: all 0.3s ease-in-out;
 backdrop-filter: blur(6px);
 box-shadow: 0 4px 6px rgba(0, 123, 255, 0.2);
}

/* Hover Effect for Buttons */
.stButton > button:hover {
 transform: scale(1.05);
 background-color: rgba(0, 123, 255, 1) !important;
 box-shadow: 0 0 10px rgba(0, 123, 255, 0.4);
 cursor: pointer;
}

/* Remove default focus outline and add custom box-shadow for Buttons */
.stButton > button:focus {
 outline: none !important;
 box-shadow: 0 0 6px rgba(0, 123, 255, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize SQLite Database

def init_db():
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        email TEXT,
                        password_hash TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS hydration_log (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        intake REAL,
                        datetime TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS goals (
                        username TEXT PRIMARY KEY,
                        daily_goal REAL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
                        username TEXT PRIMARY KEY,
                        age INTEGER,
                        gender TEXT,
                        weight REAL,
                        activity TEXT,
                        special_needs TEXT,
                        city TEXT,
                        FOREIGN KEY(username) REFERENCES users(username))''')

    # 🔹 Add email column safely if DB already exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# Function to register a new user
def register_user_db(username, password):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        st.error("Username already exists. Please choose a different one.")
        conn.close()
        return False

    # Insert new user with hashed password
    hashed_password = hash_password(password)
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()
    return True

# Function to hash password and store it securely
def hash_password(password):
    # Ensure password is bytes for bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Function to check the password against stored hash
def check_password(stored_hash, password):
    # Ensure password is bytes for bcrypt
    # stored_hash from DB might be bytes or string, handle both
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# Function to log water intake
def log_water_intake_db(username, amount):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO hydration_log (username, intake, datetime) VALUES (?, ?, ?)", (username, amount, timestamp))

    conn.commit()
    conn.close()

# Function to get user hydration history
def get_hydration_history_db(username):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, intake, datetime FROM hydration_log WHERE username=? ORDER BY datetime DESC", (username,))
    history = cursor.fetchall()

    conn.close()
    return history

# Function to get temperature and weather icon
# Consider moving API key to Streamlit Secrets
def get_temperature(city_name, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={api_key}"
        response = requests.get(url)
        data = response.json()

        if data['cod'] == 200:
            temp = data['main']['temp']
            icon = data['weather'][0]['icon']
            description = data['weather'][0]['description']
            return temp, icon, description
        else:
            st.error("Could not retrieve weather data. Please check the city name.")
            return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None, None, None

# Removed the old rule-based get_recommendation function


# Hydration tips based on activity level
def hydration_tip(activity):
    if activity == "High":
        return "💪 You're highly active! Drink extra water to stay hydrated during workouts!"
    elif activity == "Moderate":
        return "🏃 You're moderately active! Keep up the good work and stay hydrated!"
    else:
        return "🚶 You're less active today. Hydrate to maintain your well-being!"

sender_email = st.secrets["email"]["address"]
sender_password = st.secrets["email"]["password"]
# Function to send email (Requires configuration and Streamlit Secrets for credentials)

def send_hydration_reminder(email):
    sender_email = st.secrets["email"]["address"]
    sender_password = st.secrets["email"]["password"]
    smtp_server = "smtp.gmail.com"
    smtp_port = 465

    subject = "Hydration Reminder"
    body = """
    Hi there!

    This is your hydration reminder! Remember to drink enough water today to stay hydrated.

    Keep up the great work with your hydration goal!

    Cheers,
    Your Hydration App Team
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        st.success("✅ Reminder email sent!")
    except Exception as e:
        st.error(f"❌ Error sending email: {e}")

# Function to register a new user
def register_user(username, password):
    # This function is called by register_form and handles rerunning
    if register_user_db(username, password):
        st.session_state.logged_in = True
        st.session_state.current_user = username
        # Clear session state for the new user
        st.session_state.pop('user_profile', None)
        st.session_state.pop('user_details_submitted', None)
        st.success(f"✅ Account created successfully for {username}! Please log in.")
        st.rerun()


# Login form for user to authenticate
def login_form():
    st.subheader("🔐 Login to Your Account")

    username = st.text_input("Email Address", placeholder="yourname@example.com").strip()
    password = st.text_input("Password", type="password", placeholder="Enter your password").strip()

    login_clicked = st.button("Login")

    if login_clicked:
        # Check if email or password is missing
        if not username or not password:
            st.error("❗ Both email and password are required.")
            return

        # Validate email format
        if not is_valid_email(username):
            st.error("❗ Please enter a valid email address.")
            return

        try:
            # Database connection
            conn = sqlite3.connect("hydration.db")
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            result = cursor.fetchone()
            conn.close()

            # Check password hash
            if result and check_password(result[0], password):
                st.session_state.logged_in = True

                # Clear session state if a different user logs in
                if 'current_user' not in st.session_state or st.session_state.current_user != username:
                    st.session_state.pop('user_profile', None)  # Clear previous user's profile data
                    st.session_state.pop('user_details_submitted', None)  # Reset profile form state
                    # Clear any other user-specific state if needed
                    st.session_state.pop('total_intake_editor', None) # Clear the intake editor value

                st.session_state.current_user = username  # Set the new user
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()  # Trigger a rerun to reload the page with new user's data

            else:
                st.error("❌ Invalid email or password. Please try again.")
        except sqlite3.Error as e:
            st.error(f"❌ Database error: {e}")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

# Register form for new users to create an account
def register_form():
    st.subheader("🆕 Create a New Account")

    new_email = st.text_input("Email Address", placeholder="yourname@example.com").strip()
    new_password = st.text_input("New Password", type="password", placeholder="At least 8 characters, letters and numbers").strip()

    register_clicked = st.button("Register")

    if register_clicked:
        if not new_email or not new_password:
            st.error("❗ Both email and password are required to register.")
            return

        if not is_valid_email(new_email):
            st.error("❗ Please enter a valid email address.")
            return

        if not is_strong_password(new_password):
            st.error("❗ Password must be at least 8 characters long and include letters and numbers.")
            return

        # Now register
        # Call the register_user function which handles DB and rerun
        register_user(new_email, new_password)


def is_valid_email(email):
    """Validate email format."""
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email) is not None

def is_strong_password(password):
    """Validate password strength."""
    # Checks for length >= 8 and presence of at least one digit and one alpha char
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)


# Function to check if the user is logged in
def check_login():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        # Check for account choice and render appropriate form
        account_choice = st.radio("Do you have an account?", ["Login", "Register"], key='account_choice') # Added key

        if account_choice == "Login":
            login_form()
        elif account_choice == "Register":
            register_form()

        return False
    return True

def get_today_total_intake(username):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()
    today_date = datetime.now().strftime("%Y-%m-%d")
    # Sum intake for the current user for today's date
    cursor.execute("""
        SELECT SUM(intake) FROM hydration_log
        WHERE username = ? AND DATE(datetime) = ?
    """, (username, today_date))
    total = cursor.fetchone()[0]
    conn.close()
    # Ensure the return value is consistently a float
    return float(total) if total is not None else 0.0

# Validate inputs
def validate_inputs(age, weight, activity, special_needs):
    # Check if age and weight are valid numbers
    if isinstance(age, str): # Only check isdigit if it's a string
        if not age.isdigit():
            st.error("Please enter a valid age (numeric).")
            return False
        age = int(age) # Convert to int after check
    elif not isinstance(age, (int, float)): # Handle cases where age might not be string/int/float
         st.error("Invalid age format.")
         return False


    if not is_valid_float(weight):  # Check if weight is a valid float (string, int, or float type)
        st.error("Please enter a valid weight value (numeric).")
        return False
    weight = float(weight) if isinstance(weight, str) else weight # Convert to float if string

    # Ensure age and weight are within acceptable ranges
    if age is None or age <= 0: # Add None check for age after potential conversion issues
        st.error("Age must be a positive value.")
        return False
    if weight is None or weight <= 0: # Add None check for weight after potential conversion issues
        st.error("Weight must be a positive value.")
        return False


    # Check if activity level and special needs are selected
    valid_activities = ["", "Low", "Moderate", "High"] # Include empty string as a valid initial state
    if activity not in valid_activities:
        st.error("Please select a valid activity level.")
        return False

    valid_special_needs = ["", "None", "Athlete", "Pregnancy", "Kidney Condition", "High Altitude"] # Include empty string
    if special_needs not in valid_special_needs:
        st.error("Please select a valid special need option.")
        return False

    return age, weight, activity, special_needs  # Return the valid values (age and weight are now numeric)

def is_valid_float(value):
    # Check if the value can be converted to float
    if value is None or value == "": # Treat None or empty string as not a valid float input
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError): # Catch TypeError as well
        return False

try:
    # Load the model and preprocessor
    model = load('model.pkl')
    preprocessor = load('preprocessor.pkl')
    # print("[INFO] Model and preprocessor loaded successfully.") # Optional print for debugging
except FileNotFoundError:
    st.error("Model file not found. Please ensure 'model.pkl' and 'preprocessor.pkl' are in the correct directory.")
    model = None
    preprocessor = None
except Exception as e:
    st.error(f"An error occurred while loading the model files: {e}")
    model = None
    preprocessor = None


# Initialize session ID if not already set (Optional, depends on use case)
if "session_id" not in st.session_state:
    st.session_state.session_id = 0
else:
    st.session_state.session_id += 1

# Initialize a session state to track if user details have been submitted
if "user_details_submitted" not in st.session_state:
    st.session_state.user_details_submitted = False

# Initialize session state for user details
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

# Initialize SQLite Database
init_db()

def update_email(username, new_email):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, username))
    conn.commit()
    conn.close()


# Function to fetch user profile from the database
def get_user_profile_db(username):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()
    cursor.execute("SELECT age, gender, weight, activity, special_needs, city FROM user_profiles WHERE username=?", (username,))
    profile = cursor.fetchone()
    conn.close()
    if profile:
        return {
            "age": profile[0],
            "gender": profile[1],
            "weight": profile[2],
            "activity": profile[3],
            "special_needs": profile[4],
            "city": profile[5],
        }
    return {}

# Function to save user profile to the database
def save_user_profile_db(username, age, gender, weight, activity, special_needs, city):
    conn = sqlite3.connect("hydration.db")
    cursor = conn.cursor()
    # Use INSERT OR REPLACE to update if username exists, insert if not
    cursor.execute(
        """
        INSERT OR REPLACE INTO user_profiles (username, age, gender, weight, activity, special_needs, city)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (username, age, gender, weight, activity, special_needs, city),
    )
    conn.commit()
    conn.close()
# Main logic for checking login and user content
if check_login():
    st.write("Welcome to the Hydration Recommender!")

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        # Clear session state on logout
        st.session_state.pop('user_profile', None)
        st.session_state.pop('user_details_submitted', None)
        st.session_state.pop('total_intake_editor', None) # Clear the intake editor value
        # Clear state related to recommendation display
        st.session_state.pop('recommendation_calculated', None)
        st.session_state.pop('calculated_recommendation', None)
        st.session_state.pop('calculated_city', None)
        st.session_state.pop('calculated_temperature', None)
        st.session_state.pop('calculated_icon', None)
        st.session_state.pop('calculated_description', None)

        st.success("You have been logged out.")
        st.rerun() # Rerun to show login/register

    username = st.session_state.current_user

    # Load user profile if it exists in DB and not in session state
    if not st.session_state.user_profile:
        st.session_state.user_profile = get_user_profile_db(username)
        if st.session_state.user_profile:
            st.session_state.user_details_submitted = True
            # If profile was just loaded from DB and submitted state set,
            # trigger calculation if not already calculated for this user/session
            if not st.session_state.get('recommendation_calculated', False):
                 # This re-fetches profile data from DB, which might be slightly redundant
                 # but ensures we have the data for initial calculation on load.
                 # A cleaner approach might store these validated numeric values after profile save.
                 # For now, let's re-fetch and validate.
                 profile_data = get_user_profile_db(username)
                 if profile_data:
                     age_db = profile_data.get("age")
                     gender_db = profile_data.get("gender")
                     weight_db = profile_data.get("weight")
                     activity_db = profile_data.get("activity")
                     special_needs_db = profile_data.get("special_needs")
                     city_name_db = profile_data.get("city")

                     # Validate inputs from the loaded profile
                     validated_inputs_db = validate_inputs(age_db, weight_db, activity_db, special_needs_db)

                     if validated_inputs_db:
                         age_val_db, weight_val_db, activity_val_db, special_needs_val_db = validated_inputs_db
                         # Trigger calculation using DB data
                         temperature_db, icon_db, description_db = get_temperature(city_name_db, "cd7dc1f4c509bfe97497ca92cbbb775e") # Use your API key

                         if temperature_db is not None and model and preprocessor:
                             try:
                                # Prepare input for model - Use correct column names and validated DB data
                                input_df_db = pd.DataFrame({
                                    'Age': [age_val_db],
                                    'Gender': [gender_db],
                                    'Weight (kg)': [weight_val_db],
                                    'Activity Level': [activity_val_db],
                                    'Temperature (°C)': [temperature_db],
                                    'Special Needs': [special_needs_val_db]
                                })

                                # Preprocess and predict
                                processed_input_db = preprocessor.transform(input_df_db)
                                prediction_db = model.predict(processed_input_db)
                                recommendation_db = max(prediction_db[0], 2.0)
                                rounded_recommendation_db = round(recommendation_db, 1)

                                # Store calculated results in session state
                                st.session_state.recommendation_calculated = True
                                st.session_state.calculated_recommendation = rounded_recommendation_db
                                st.session_state.calculated_city = city_name_db
                                st.session_state.calculated_temperature = temperature_db
                                st.session_state.calculated_icon = icon_db
                                st.session_state.calculated_description = description_db

                                # No need to rerun here, the display section will handle it on this run

                             except Exception as e:
                                 st.error(f"Error calculating recommendation on profile load: {e}")
                                 st.session_state.recommendation_calculated = False # Ensure flag is false on error

                         elif temperature_db is None:
                              st.warning("Unable to retrieve weather for recommendation on profile load.")
                              st.session_state.recommendation_calculated = False
                         else: # Model or preprocessor not loaded
                             st.error("Model files not loaded. Cannot calculate recommendation on profile load.")
                             st.session_state.recommendation_calculated = False


    # --- User Profile Form ---
    if not st.session_state.user_details_submitted:
        st.subheader("Tell us a bit about yourself:")
        # Retrieve current values from session state profile if they exist
        age_val = st.session_state.user_profile.get("age", "")
        gender_val = st.session_state.user_profile.get("gender", "")
        weight_val = st.session_state.user_profile.get("weight", "")
        activity_val = st.session_state.user_profile.get("activity", "")
        special_needs_val = st.session_state.user_profile.get("special_needs", "")
        city_name_val = st.session_state.user_profile.get("city", "")


        # Determine current index for selectboxes
        gender_options = ["", "Male", "Female", "Other"]
        gender_index = gender_options.index(gender_val) if gender_val in gender_options else 0

        activity_options = ["", "Low", "Moderate", "High"]
        activity_index = activity_options.index(activity_val) if activity_val in activity_options else 0

        special_needs_options = ["", "None", "Athlete", "Pregnancy", "Kidney Condition", "High Altitude"]
        special_needs_index = special_needs_options.index(special_needs_val) if special_needs_val in special_needs_options else 0


        age = st.text_input("Age", value=age_val, key='profile_age')
        gender = st.selectbox("Gender", options=gender_options, index=gender_index, key='profile_gender')
        weight = st.text_input("Weight (kg)", value=weight_val, key='profile_weight')
        activity = st.selectbox("Activity Level", options=activity_options, index=activity_index, key='profile_activity')
        special_needs = st.selectbox("Special Needs", options=special_needs_options, index=special_needs_index, key='profile_special_needs')
        city_name = st.text_input("Enter your city", value=city_name_val, key='profile_city')


        if st.button("Save Profile"):
            # Validate inputs from the form widgets
            if not all([age, gender, weight, activity, special_needs, city_name]):
                 st.warning("Please fill in all fields.")
            # Call validate_inputs with values from the form widgets
            # validate_inputs will return validated numeric/string values if successful
            validated_inputs = validate_inputs(age, weight, activity, special_needs)

            if validated_inputs: # If validation passes
                 age_val_form, weight_val_form, activity_val_form, special_needs_val_form = validated_inputs
                 # Save the profile to the database using the original string values from the form
                 save_user_profile_db(username, age, gender, weight, activity, special_needs, city_name)
                 # Update session state profile with the saved original string values
                 st.session_state.user_profile = {
                     "age": age,
                     "gender": gender,
                     "weight": weight,
                     "activity": activity,
                     "special_needs": special_needs,
                     "city": city_name,
                 }
                 st.session_state.user_details_submitted = True

                 # --- Trigger Recommendation Calculation Immediately After Saving ---
                 with st.spinner("Profile saved! Calculating recommendation..."):
                     temperature, icon, description = get_temperature(city_name, "cd7dc1f4c509bfe97497ca92cbbb775e") # Use your API key

                     if temperature is not None:
                         # Check if model and preprocessor are available
                         if model and preprocessor:
                             try:
                                 # Prepare input for model - Use correct column names and validated numeric/string values
                                 input_df = pd.DataFrame({
                                     'Age': [age_val_form], # Use validated numeric age from form
                                     'Gender': [gender], # Use string gender from form
                                     'Weight (kg)': [weight_val_form], # Use validated numeric weight from form
                                     'Activity Level': [activity], # Use string activity from form
                                     'Temperature (°C)': [temperature], # Use numeric temperature
                                     'Special Needs': [special_needs], # Use string special_needs from form
                                 })

                                 # Preprocess input
                                 processed_input = preprocessor.transform(input_df)

                                 # Predict water intake
                                 prediction = model.predict(processed_input)
                                 # Ensure prediction is a positive value, minimum 2L
                                 recommendation = max(prediction[0], 2.0)
                                 rounded_recommendation = round(recommendation, 1)

                                 # Store calculated results in session state
                                 st.session_state.recommendation_calculated = True
                                 st.session_state.calculated_recommendation = rounded_recommendation
                                 st.session_state.calculated_city = city_name
                                 st.session_state.calculated_temperature = temperature
                                 st.session_state.calculated_icon = icon
                                 st.session_state.calculated_description = description

                                 st.success("Profile saved and recommendation calculated!")
                                 st.rerun() # Rerun to display the main content and results section

                             except Exception as e:
                                 st.error(f"Error during recommendation calculation after saving profile: {e}")
                                 st.session_state.recommendation_calculated = False # Ensure flag is false on error
                                 st.rerun() # Rerun even if calculation fails to show main content

                         else: # Model or preprocessor not loaded
                             st.error("Model files not loaded. Cannot calculate recommendation after saving profile.")
                             st.session_state.recommendation_calculated = False
                             st.rerun() # Rerun even if calculation fails to show main content

                     elif temperature is None:
                         st.warning("Profile saved, but unable to retrieve weather for immediate recommendation.")
                         st.session_state.recommendation_calculated = False
                         st.rerun() # Rerun even if weather fails to show main content
            else:
                 # validate_inputs will show the specific error message
                 pass # Error message already shown by validate_inputs


    # --- Display Calculated Results and Logging Input (Conditional based on recommendation_calculated flag) ---
    # This block displays if the profile is submitted AND a recommendation has been calculated
    if st.session_state.user_details_submitted and st.session_state.get('recommendation_calculated', False):

        # Retrieve stored calculation results from session state
        rounded_recommendation = st.session_state.calculated_recommendation
        city_name_calc = st.session_state.calculated_city
        temperature_calc = st.session_state.calculated_temperature
        icon_calc = st.session_state.calculated_icon
        description_calc = st.session_state.calculated_description

        # Retrieve original activity string from user profile for tip
        original_activity_for_tip = st.session_state.user_profile.get("activity", "Low")


        # Display the stored results
        st.subheader("Your Hydration Recommendation")
        st.success(f"🤖 Recommended Water Intake: {rounded_recommendation} liters")
        st.write(f"🌡 Current Temperature in {city_name_calc}: {temperature_calc}°C")
        st.image(f"http://openweathermap.org/img/wn/{icon_calc}@2x.png", caption=f"{description_calc.capitalize()}")
        st.info(hydration_tip(original_activity_for_tip)) # Use the original activity string for the tip

                # --- Send Reminder Section ---
        st.subheader("🔔 Hydration Reminder")

        if "current_user" in st.session_state:
            username = st.session_state.current_user

            # Fetch email
            conn = sqlite3.connect("hydration.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username=?", (username,))
            result = cursor.fetchone()
            conn.close()

            user_email = result[0] if result else None

            # ---- SEND REMINDER BUTTON ----
            if st.button("Send me a reminder now"):
                if user_email:
                    try:
                        send_hydration_reminder(user_email)
                        st.success("✅ Reminder sent successfully!")
                    except Exception as e:
                        st.error(f"❌ Failed to send reminder: {str(e)}")
                else:
                    st.warning("⚠️ No email found. Please update your email below.")

            # ---- EMAIL UPDATE SECTION (shown only if email missing) ----
            if not user_email:
                new_email = st.text_input("Enter your email to receive reminders:")

                if st.button("Update Email"):
                    if new_email:
                        try:
                            conn = sqlite3.connect("hydration.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET email=? WHERE username=?",
                                (new_email, username)
                            )
                            conn.commit()
                            conn.close()

                            st.success("✅ Email updated successfully!")
                            st.rerun()  # IMPORTANT
                        except Exception as e:
                            st.error(f"❌ Failed to update email: {str(e)}")
                    else:
                        st.warning("Please enter a valid email.")

# Show today's hydration summary
        st.subheader("📊 Today's Hydration Summary")
        # Fetch the latest total from the database
        today_total = get_today_total_intake(username)
        remaining_intake = max(rounded_recommendation - today_total, 0)
        percentage = min((today_total / rounded_recommendation) * 100, 100)

        st.metric(label="Water Intake Today", value=f"{today_total:.2f} L",
                  delta=f"+{remaining_intake:.2f} L to go")  # More explicit delta label

        st.write(f"🌟 Daily Goal: {rounded_recommendation} L")
        st.write(f"💧 You've consumed: {today_total:.2f} L")
        st.write(f"💧 Remaining: {remaining_intake:.2f} L")  # Explicit remaining display
        st.write(f"🎯 Progress: {percentage:.1f}% of your goal")

        # Progress Bar with Dynamic Color
        progress_color = "green" if percentage >= 100 else "yellow" if percentage >= 75 else "red"
        st.progress(percentage / 100)
        st.markdown(f"<style>.stProgressBar > div {{ background-color: {progress_color}; }}</style>", unsafe_allow_html=True)

                # --- Hydration History - Daily Bar Chart ---
        st.subheader("💧 Hydration History")

        history = get_hydration_history_db(username)

        if history:
            history_df = pd.DataFrame(
                history,
                columns=["id", "username", "intake", "datetime"]
            )
            history_df["datetime"] = pd.to_datetime(history_df["datetime"])

            # Extract date only
            history_df["date"] = history_df["datetime"].dt.strftime("%Y-%m-%d")

            # Group by date and sum intake
            daily_df = history_df.groupby("date")["intake"].sum().reset_index()

            fig = px.bar(
                daily_df,
                x="date",
                y="intake",
                title="💧 Daily Water Intake",
                labels={"date": "Date", "intake": "Water Intake (Liters)"},
                template="plotly_white"
            )
            fig.update_traces(width=0.4)


            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Water Intake (Liters)",
                title_x=0.5,
                height=400,
                xaxis=dict(type="category")
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No hydration data available yet.")

        # --- Water intake input and logging button ---

        st.subheader("➕ Log Water Intake")

        water_amount = st.number_input(
            "How much water did you just drink? (liters)",
            min_value=0.0,
            step=0.1
        )

        if st.button("Add Intake"):
            if water_amount > 0:
                log_water_intake_db(username, water_amount)
                st.success(f"💧 Logged {water_amount:.2f} L")
                st.rerun()
            else:
                st.warning("Please enter a valid amount.")

        # --- End of Calculated Results and Logging Section ---


    if st.session_state.user_details_submitted: # Only show update button if profile is submitted
        if st.button("Update Profile"):
            st.session_state.user_details_submitted = False
            # Clear state related to recommendation display when updating profile
            st.session_state.pop('recommendation_calculated', None)
            st.session_state.pop('calculated_recommendation', None)
            st.session_state.pop('calculated_city', None)
            st.session_state.pop('calculated_temperature', None)
            st.session_state.pop('calculated_icon', None)
            st.session_state.pop('calculated_description', None)
            st.rerun() # Rerun to show the profile form


# --- Content for not logged-in users ---
else:
    st.info("Please log in or register to access the app.")