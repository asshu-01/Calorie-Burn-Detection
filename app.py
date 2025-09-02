import streamlit as st
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import json
import hashlib
from datetime import datetime, timedelta
import altair as alt

# --- PAGE CONFIGURATION ---
# Use "wide" layout for a dashboard feel
st.set_page_config(page_title="Fitness Dashboard", layout="wide")


# --- 3D ANIMATED BACKGROUND ---
def add_animated_background():
    # This function remains the same, providing the visual background.
    fragment_shader = """
    precision mediump float;
    uniform vec2 u_resolution;
    uniform float u_time;
    float random (in vec2 st) { return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123); }
    float noise (in vec2 st) {
        vec2 i = floor(st); vec2 f = fract(st);
        float a = random(i); float b = random(i + vec2(1.0, 0.0));
        float c = random(i + vec2(0.0, 1.0)); float d = random(i + vec2(1.0, 1.0));
        vec2 u = f*f*(3.0-2.0*f);
        return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
    }
    #define OCTAVES 6
    float fbm (in vec2 st) {
        float value = 0.0; float amplitude = .5;
        for (int i = 0; i < OCTAVES; i++) { value += amplitude * noise(st); st *= 2.; amplitude *= .5; }
        return value;
    }
    void main() {
        vec2 st = gl_FragCoord.xy/u_resolution.xy; st.x *= u_resolution.x/u_resolution.y;
        vec3 color = vec3(0.0);
        vec2 q = vec2(0.); q.x = fbm( st + 0.00*u_time); q.y = fbm( st + vec2(1.0));
        vec2 r = vec2(0.); r.x = fbm( st + 1.0*q + vec2(1.7,9.2)+ 0.15*u_time ); r.y = fbm( st + 1.0*q + vec2(8.3,2.8)+ 0.126*u_time);
        float f = fbm(st+r);
        color = mix(vec3(0.1,0.62,0.67), vec3(0.67,0.67,0.5), clamp((f*f)*4.0,0.0,1.0));
        color = mix(color, vec3(0,0,0.16), clamp(length(q),0.0,1.0));
        color = mix(color, vec3(0.67,1,1), clamp(length(r.x),0.0,1.0));
        gl_FragColor = vec4((f*f*f+.6*f*f+.5*f)*color,1.);
    }
    """
    html_code = f"""
    <style>
        .stApp {{ background: #0E1117; }}
        #bg-canvas {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; opacity: 0.8; }}
        div.st-emotion-cache-1r6slb0, div.st-emotion-cache-12w0qpk, div.st-emotion-cache-1d3wcrq {{
            background-color: rgba(14, 17, 23, 0.7); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 25px; margin-top: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
         div[data-testid="stForm"] {{
            background-color: transparent; backdrop-filter: none; border: none; box-shadow: none; padding: 0;
        }}
        h1, h2, h3, p, label {{ color: white !important; }}
    </style>
    <canvas id="bg-canvas"></canvas>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/glslCanvas/0.2.4/glslCanvas.min.js"></script>
    <script>
        var canvas = document.getElementById("bg-canvas"); var sandbox = new GlslCanvas(canvas);
        sandbox.load(`{fragment_shader}`);
        sandbox.setUniform("u_time", 0.0); sandbox.setUniform("u_resolution", [window.innerWidth, window.innerHeight]);
        function animate(time) {{ sandbox.setUniform("u_time", time / 1000); requestAnimationFrame(animate); }}
        animate(0);
        window.addEventListener('resize', () => {{ sandbox.setUniform("u_resolution", [window.innerWidth, window.innerHeight]); }});
    </script>
    """
    st.components.v1.html(html_code, height=0)


# --- USER & WORKOUT DATA HANDLING ---
def hash_password(password): return hashlib.sha256(str.encode(password)).hexdigest()
def verify_password(stored, provided): return stored == hash_password(provided)

def load_users():
    users_file = Path("users.json")
    if not users_file.is_file(): return {}
    try:
        with open(users_file, "r") as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return {}

def save_users(users):
    try:
        with open("users.json", "w") as f: json.dump(users, f, indent=4)
        return True
    except (IOError, TypeError) as e:
        st.error(f"Error saving data: {e}")
        return False

def add_workout_to_history(username, workout_data):
    users = load_users()
    if 'history' not in users[username]:
        users[username]['history'] = []
    users[username]['history'].append(workout_data)
    save_users(users)


# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'page' not in st.session_state: st.session_state['page'] = 'login'


# --- AUTHENTICATION PAGE ---
def go_to_signup(): st.session_state.page = "signup"
def go_to_login(): st.session_state.page = "login"

def authentication_page():
    add_animated_background()
    # (Authentication page logic is the same as before, with one addition)
    logo_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="orange" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2c-4.4 3.4-6.4 7.6-6.4 11.2 0 4.4 3.6 8 8 8s8-3.6 8-8c0-3.6-2-7.8-6.4-11.2z"/>
        <path d="M12 12c-2.2 2.1-3.2 4.6-3.2 6.8 0 2.2 1.8 4 4 4s4-1.8 4-4c0-2.2-1-4.7-3.2-6.8z"/>
    </svg>
    """
    st.markdown(f"<div style='text-align: center;'>{logo_svg}</div>", unsafe_allow_html=True)
    if st.session_state['page'] == 'login':
        st.title("Welcome Back!")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                users = load_users()
                if username in users and verify_password(users[username]['password'], password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else: st.error("😕 Invalid username or password")
        st.button("Create a New Account", on_click=go_to_signup, use_container_width=True)
    elif st.session_state['page'] == 'signup':
        st.title("Create a New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Create a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Sign Up", use_container_width=True):
                users = load_users()
                if not new_username: st.error("Username cannot be empty.")
                elif new_username in users: st.error("Username already exists.")
                elif new_password != confirm_password: st.error("Passwords do not match.")
                elif len(new_password) < 6: st.error("Password must be at least 6 characters long.")
                else:
                    # Add default goal and history for new users
                    users[new_username] = {'password': hash_password(new_password), 'history': [], 'goal': 2000}
                    if save_users(users):
                        st.success("Account created! Please sign in."); st.toast("Welcome aboard! 🎉")
                        go_to_login()
        st.button("Already have an account? Sign In", on_click=go_to_login, use_container_width=True)

# --- MAIN DASHBOARD PAGE ---
def dashboard_page():
    add_animated_background()
    
    users = load_users()
    current_user = st.session_state.get('username', 'User')
    user_data = users.get(current_user, {})

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"Welcome, {current_user}!")
        
        # Goal setting in sidebar
        new_goal = st.number_input("Set Weekly Calorie Goal", 
                                   value=user_data.get('goal', 2000), 
                                   min_value=500, step=100)
        if new_goal != user_data.get('goal'):
            users[current_user]['goal'] = new_goal
            save_users(users)
            st.toast("Goal updated!")

        st.markdown("---")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['page'] = 'login'
            st.session_state.pop('username', None)
            st.rerun()

    # --- LOG NEW WORKOUT (EXPANDER) ---
    with st.expander("🏋️‍♀️ Log a New Workout Session", expanded=False):
        model_file = Path('calories_model.pkl')
        model = None
        if model_file.is_file():
            try:
                with open('calories_model.pkl', 'rb') as file: model = pickle.load(file)
            except Exception as e: st.error(f"Error loading model: {e}")
        
        with st.form("prediction_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                workout_type = st.selectbox("Workout Type", ("Cardio", "Strength Training", "Yoga", "Sports", "Other"))
                gender = st.selectbox("Gender", ("Female", "Male"))
                age = st.number_input("Age (years)", 1, 100, 25)
            with c2:
                height = st.number_input("Height (cm)", 100, 250, 170)
                weight = st.number_input("Weight (kg)", 30, 200, 65)
                duration = st.number_input("Duration (min)", 1, 300, 30)
            with c3:
                heart_rate = st.number_input("Heart Rate (bpm)", 50, 200, 100)
                body_temp = st.number_input("Body Temp (°C)", 35.0, 42.0, 37.0, format="%.1f")
            
            submitted = st.form_submit_button('Predict & Log Calories', type="primary", use_container_width=True)
            if submitted:
                if model:
                    input_data = np.array([[1 if gender == 'Male' else 0, age, height, weight, duration, heart_rate, body_temp]])
                    prediction = model.predict(input_data)[0]
                    st.success(f"### Estimated Calories Burnt: **{prediction:.2f} kcal**")
                    workout_data = {
                        "timestamp": datetime.now().isoformat(), "workout_type": workout_type,
                        "duration": duration, "heart_rate": heart_rate, "calories_burnt": round(prediction, 2)
                    }
                    add_workout_to_history(current_user, workout_data)
                    st.rerun()
                else: st.error("Prediction failed. Model not loaded.")

    st.header("📊 Your Activity Dashboard")

    # --- DASHBOARD METRICS & CHARTS ---
    history = user_data.get('history', [])
    if not history:
        st.info("Your dashboard is empty. Log a workout above to get started!")
    else:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # --- FIX FOR MISSING workout_type KEY ---
        if 'workout_type' not in df.columns:
            df['workout_type'] = 'Uncategorized'
        df['workout_type'].fillna('Uncategorized', inplace=True)


        # --- Weekly Goal Progress ---
        st.subheader("Weekly Goal Progress")
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        weekly_df = df[df['timestamp'] >= start_of_week]
        calories_this_week = weekly_df['calories_burnt'].sum()
        goal = user_data.get('goal', 2000)
        progress = min(calories_this_week / goal, 1.0)
        st.progress(progress)
        st.markdown(f"**{calories_this_week:,.0f} / {goal:,.0f} kcal** burned this week.")

        st.markdown("---")

        # --- Key Metrics ---
        total_calories = df['calories_burnt'].sum()
        total_duration = df['duration'].sum()
        total_workouts = len(df)
        avg_calories = df['calories_burnt'].mean()

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Lifetime Calories", f"{total_calories:,.0f} kcal")
        kpi2.metric("Lifetime Duration", f"{total_duration:,.0f} min")
        kpi3.metric("Total Workouts", f"{total_workouts}")
        kpi4.metric("Avg. Burn / Workout", f"{avg_calories:,.1f} kcal")

        # --- Charts ---
        chart1, chart2 = st.columns(2)
        with chart1:
            st.subheader("Workout Types")
            workout_dist = df['workout_type'].value_counts().reset_index()
            workout_dist.columns = ['type', 'count']
            donut_chart = alt.Chart(workout_dist).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="type", type="nominal", title="Workout Type"),
                tooltip=['type', 'count']
            ).properties(height=300)
            st.altair_chart(donut_chart, use_container_width=True)

        with chart2:
            st.subheader("Calories Burnt Over Time")
            line_chart = alt.Chart(df).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('timestamp:T', title='Date'),
                y=alt.Y('calories_burnt:Q', title='Calories Burnt (kcal)'),
                tooltip=[alt.Tooltip('timestamp:T', title='Date'), alt.Tooltip('calories_burnt:Q', title='Calories')]
            ).interactive().properties(height=300)
            st.altair_chart(line_chart, use_container_width=True)

        # --- Calendar Heatmap ---
        st.subheader("Workout Consistency")
        df['date'] = df['timestamp'].dt.date
        daily_calories = df.groupby('date')['calories_burnt'].sum().reset_index()
        
        if not daily_calories.empty:
            # Ensure all dates are present for the calendar
            all_dates = pd.date_range(start=daily_calories['date'].min(), end=daily_calories['date'].max())
            all_dates_df = pd.DataFrame(all_dates, columns=['date'])
            daily_calories['date'] = pd.to_datetime(daily_calories['date'])
            daily_calories = pd.merge(all_dates_df, daily_calories, on='date', how='left').fillna(0)
            
            daily_calories['year'] = daily_calories['date'].dt.isocalendar().year
            daily_calories['week'] = daily_calories['date'].dt.isocalendar().week
            daily_calories['day'] = daily_calories['date'].dt.day_name()
            
            heatmap = alt.Chart(daily_calories, title="Daily Calories Burned").mark_rect().encode(
                x=alt.X('week:O', title='Week of Year'),
                y=alt.Y('day:O', title='Day of Week', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
                color=alt.Color('calories_burnt:Q', legend=alt.Legend(title="Calories"), scale=alt.Scale(scheme='greenblue')),
                tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip('calories_burnt:Q', title='Calories Burned')]
            ).properties(
                width='container',
            )
            st.altair_chart(heatmap, use_container_width=True)


# --- SCRIPT ROUTER ---
if st.session_state.get('logged_in', False):
    dashboard_page()
else:
    authentication_page()

