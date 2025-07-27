import streamlit as st
import pandas as pd
import os
import datetime

# Optional Firebase Auth integration placeholder
# from firebase_admin import auth, credentials, initialize_app

# Page config for a polished look
st.set_page_config(page_title="Calorie Tracker", layout="wide")

@st.cache_data
def load_data():
    if not os.path.exists("cleaned_food_data.csv"):
        st.error("🚫 'cleaned_food_data.csv' not found. Please upload it to your GitHub repo root.")
        st.stop()
    return pd.read_csv("cleaned_food_data.csv")

food_df = load_data()

# Initialize session state
if 'food_log' not in st.session_state:
    st.session_state.food_log = []
if 'supplement_log' not in st.session_state:
    st.session_state.supplement_log = []
if 'weight_log' not in st.session_state:
    st.session_state.weight_log = []

# Optional: user targets
macro_targets = {
    "Calories": 2000,
    "Protein": 150,
    "Carbs": 200,
    "Fats": 70
}

st.markdown("""
    <style>
    .main { background-color: #f9fbfc; }
    .stApp { font-family: 'Segoe UI', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("💪 Calorie & Supplement Tracker")
st.subheader("Track your food, supplements, and body stats to hit your fitness goals.")

# Tabs layout
tabs = st.tabs(["🍴 Food Intake", "📚 Past Logs", "💊 Supplements", "📈 Weight Progress"])

# Shared date picker
selected_date = st.date_input("Select Date", datetime.date.today(), key="date")

# --- Food Intake Tab ---
with tabs[0]:
    st.header("🍽️ Log Your Meals")
    with st.form("food_form"):
        ingredient_list = food_df["Ingredient"].dropna().unique() if "Ingredient" in food_df.columns else []
        if len(ingredient_list) == 0:
            st.warning("⚠️ No ingredients available to select. Please check your CSV file.")
            ingredient = None
        else:
            ingredient = st.selectbox("Select Ingredient", sorted(ingredient_list))
        intake = st.number_input("Quantity Consumed (g)", min_value=1.0, step=1.0)
        meal_type = st.radio("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
        submit_food = st.form_submit_button("➕ Add to Log")

        if submit_food:
            row = food_df[food_df["Ingredient"] == ingredient].iloc[0]
            protein_per_g = pd.to_numeric(row["Protein_per_g"], errors="coerce")
            carbs_per_g = pd.to_numeric(row["Carbs_per_g"], errors="coerce")
            fats_per_g = pd.to_numeric(row["Fats_per_g"], errors="coerce")
            calories_per_portion = pd.to_numeric(row["Calories"], errors="coerce")
            intake_portion = pd.to_numeric(row["Intake_g"], errors="coerce")

            if pd.isnull([protein_per_g, carbs_per_g, fats_per_g, calories_per_portion, intake_portion]).any():
                st.warning("⚠️ Some nutrition values are invalid. Please check the CSV for missing or non-numeric entries.")
                st.stop()

            protein = protein_per_g * intake
            carbs = carbs_per_g * intake
            fats = fats_per_g * intake
            calories = calories_per_portion * (intake / intake_portion)

            st.session_state.food_log.append({
                "Date": selected_date,
                "Ingredient": ingredient,
                "Qty (g)": intake,
                "Meal": meal_type,
                "Protein": protein,
                "Carbs": carbs,
                "Fats": fats,
                "Calories": calories
            })

    log_df = pd.DataFrame(st.session_state.food_log)
    if not log_df.empty:
        st.subheader("📋 Today's Food Log")
        daily_log = log_df[log_df['Date'] == selected_date]
        st.dataframe(daily_log, use_container_width=True)

        daily = daily_log.sum(numeric_only=True)
        cols = st.columns(4)
        cols[0].metric("🔥 Calories", f"{daily['Calories']:.0f} kcal", delta=f"Target: {macro_targets['Calories']}")
        cols[1].metric("🍗 Protein", f"{daily['Protein']:.1f} g", delta=f"Target: {macro_targets['Protein']}")
        cols[2].metric("🥖 Carbs", f"{daily['Carbs']:.1f} g", delta=f"Target: {macro_targets['Carbs']}")
        cols[3].metric("🥑 Fats", f"{daily['Fats']:.1f} g", delta=f"Target: {macro_targets['Fats']}")

        # Alerts
        for macro in ["Calories", "Protein", "Carbs", "Fats"]:
            if daily[macro] > macro_targets[macro]:
                st.warning(f"⚠️ {macro} intake exceeds your target ({macro_targets[macro]})")

        st.download_button("⬇️ Export Today's Log", daily_log.to_csv(index=False), "today_log.csv")

# Hosting Instructions
with st.expander("🚀 How to Host This App on Streamlit Cloud"):
    st.markdown("""
    1. Push all files to a GitHub repository (including `calorie_tracker_app.py`, `cleaned_food_data.csv`, `requirements.txt`)
    2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
    3. Click **'New App'**, connect your GitHub, and choose your repo and branch
    4. Set `calorie_tracker_app.py` as the main file
    5. Click **Deploy** and enjoy your live tracker!
    """)

# --- Weight Progress Tab ---
with tabs[3]:
    st.header("📈 Log and Track Your Weight")
    with st.form("weight_form"):
        weight = st.number_input("Enter your weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
        weight_submit = st.form_submit_button("📥 Log Weight")

        if weight_submit:
            st.session_state.weight_log.append({
                "Date": selected_date,
                "Weight": weight
            })

    weight_df = pd.DataFrame(st.session_state.weight_log)
    if not weight_df.empty:
        weight_df_sorted = weight_df.sort_values("Date")
        st.subheader("📊 Weight Over Time")
        st.line_chart(weight_df_sorted.set_index("Date"))
        st.dataframe(weight_df_sorted, use_container_width=True)

        st.subheader("📉 Weight Change Summary")
        st.write(f"Initial: {weight_df_sorted['Weight'].iloc[0]:.1f} kg")
        st.write(f"Latest: {weight_df_sorted['Weight'].iloc[-1]:.1f} kg")
        st.write(f"Change: {(weight_df_sorted['Weight'].iloc[-1] - weight_df_sorted['Weight'].iloc[0]):+.1f} kg")

# --- Supplement Tab with Analysis & Reminder ---
with tabs[2]:
    st.header("💊 Supplement Intake")
    with st.form("supplement_form"):
        supplement = st.text_input("Supplement Name")
        dose = st.text_input("Dose (e.g., 1 tablet, 5g scoop)")
        time = st.selectbox("Time", ["Morning", "Afternoon", "Evening", "Before Workout", "After Workout"])
        submit_supplement = st.form_submit_button("➕ Add to Log")

        if submit_supplement:
            st.session_state.supplement_log.append({
                "Date": selected_date,
                "Supplement": supplement,
                "Dose": dose,
                "Time": time
            })

    supp_df = pd.DataFrame(st.session_state.supplement_log)
    if not supp_df.empty:
        st.subheader("🧾 Supplement History")
        st.dataframe(supp_df.sort_values("Date"), use_container_width=True)

        st.subheader("📊 Supplement Frequency")
        freq = supp_df.groupby("Supplement").size().reset_index(name="Times Taken")
        st.bar_chart(freq.set_index("Supplement"))

        # Auto Reminder Simulation (simple feedback)
        today_supps = supp_df[supp_df["Date"] == selected_date]
        if today_supps.empty:
            st.warning("⚠️ You haven't logged any supplements today. Don't forget!")
        else:
            st.success(f"✅ {len(today_supps)} supplement(s) logged today. Keep it up!")
