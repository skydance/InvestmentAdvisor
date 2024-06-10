import streamlit as st
import requests
import json
import boto3
from datetime import datetime
from captcha.image import ImageCaptcha
import random
import string
import base64
from io import BytesIO


API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
API_KEY = st.secrets["API_KEY"]

# Function to generate CAPTCHA
def generate_captcha():
    image = ImageCaptcha()
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    captcha_image = image.generate_image(captcha_text)
    buffered = BytesIO()
    captcha_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return captcha_text, img_str

# Initial CAPTCHA generation
if 'captcha_text' not in st.session_state:
    captcha_text, captcha_image = generate_captcha()
    st.session_state['captcha_text'] = captcha_text
    st.session_state['captcha_image'] = captcha_image




# Configure AWS S3
s3 = boto3.client('s3')
BUCKET_NAME = st.secrets["BUCKET_NAME"]

st.title("AI-Powered Virtual Financial Assistant using GPT4o")
left_column, right_column = st.columns(2)

# User Profile Form
with left_column:
    with st.form(key='profile_form'):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=18, max_value=100, step=1)
        employment_status = st.selectbox("Employment Status", ["Employed", "Self-Employed", "Unemployed", "Retired"])
        annual_income = st.slider("Annual Income ($)", min_value=0, max_value=1000000, step=1000, format="$%d", key="annual_income_slider")
        monthly_expenses = st.slider("Monthly Expenses ($)", min_value=0, max_value=20000, step=100, format="$%d", key="monthly_expenses_slider")
        savings = st.slider("Current Savings ($)", min_value=0, max_value=1000000, step=500, format="$%d", key="savings_slider")
        investments = st.slider("Current Investments ($)", min_value=0, max_value=1000000, step=500, format="$%d", key="investments_slider")
        current_debts = st.slider("Current Debts ($)", min_value=0, max_value=1000000, step=500, format="$%d", key="current_debts_slider")

        risk_tolerance = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
        investment_goals = st.multiselect("Investment Goals", ["Retirement", "Education", "Wealth Accumulation", "Short-term Needs"])
        investment_horizon = st.selectbox("Investment Horizon", ["Short-term (1-3 years)", "Medium-term (3-5 years)", "Long-term (5+ years)"])
        preferred_investments = st.multiselect("Preferred Investment Types", ["Stocks", "Bonds", "Mutual Funds", "Cryptocurrency"])
        country = st.selectbox("Prefered Country to invest", ["United States", "Singapore", "Australia", "Indonesia", "Other"])
        # Display CAPTCHA
        st.markdown(f"![CAPTCHA](data:image/png;base64,{st.session_state['captcha_image']})")
        captcha_input = st.text_input("Enter CAPTCHA")
        submit_button = st.form_submit_button(label='Submit')
        
with right_column:
    if submit_button:
        if captcha_input == st.session_state['captcha_text']:
            user_profile = {
                "name": name,
                "age": age,
                "employment_status": employment_status,
                "annual_income": annual_income,
                "monthly_expenses": monthly_expenses,
                "savings": savings,
                "investments": investments,
                "risk_tolerance": risk_tolerance,
                "investment_goals": investment_goals,
                "investment_horizon": investment_horizon,
                "preferred_investments": preferred_investments,
                "current_debts": current_debts,
                "country": country
            }

            st.write("User Profile Submitted")
            st.json(user_profile)

            # Prepare data to send to the OpenAI API
            data_to_send = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are an expert financial advisor."},
                    {"role": "user", "content": f"""
                    Provide detailed investment advice based on the following user profile:

                    Name: {name}
                    Age: {age}
                    Employment Status: {employment_status}
                    Annual Income: ${annual_income:,}
                    Monthly Expenses: ${monthly_expenses:,}
                    Current Savings: ${savings:,}
                    Current Investments: ${investments:,}
                    Current Debts: ${current_debts:,}
                    Risk Tolerance: {risk_tolerance}
                    Investment Goals: {", ".join(investment_goals)}
                    Investment Horizon: {investment_horizon}
                    Preferred Investments: {", ".join(preferred_investments)}
                    Country: {country}

                    Please include specific stock recommendations (if chosen),  asset allocation strategy, and risk management.
                    """}
                ]
            }

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            # Send the request to the OpenAI API
            response = requests.post(API_ENDPOINT, headers=headers, json=data_to_send)
            
            if response.status_code == 200:
                response_data = response.json()
                investment_advice = response_data['choices'][0]['message']['content']
                st.write("Investment Advice:")
                st.write(investment_advice)
            else:
                st.write("Error:", response.status_code)
                st.write(response.text)
    else:
        st.error("CAPTCHA verification failed. Please try again.")
        # Regenerate CAPTCHA if failed
        captcha_text, captcha_image = generate_captcha()
        st.session_state['captcha_text'] = captcha_text
        st.session_state['captcha_image'] = captcha_image
        st.experimental_rerun()