import streamlit as st
import requests
import json
import boto3
from datetime import datetime


API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
API_KEY = st.secrets["API_KEY"]

RECAPTCHA_SITE_KEY = st.secrets["RECAPTCHA_SITE_KEY"]
RECAPTCHA_SECRET_KEY = st.secrets["RECAPTCHA_SECRET_KEY"]

# HTML for reCAPTCHA
recaptcha_html = f"""
<div class="g-recaptcha" data-sitekey="{RECAPTCHA_SITE_KEY}" data-callback="onSubmit" data-size="invisible"></div>
<script src="https://www.google.com/recaptcha/api.js" async defer></script>
<script>
    function onSubmit(token) {{
        document.getElementById("recaptcha_response").value = token;
        document.getElementById("profile_form").submit();
    }}
</script>
"""
# CSS to hide the reCAPTCHA response input
hide_input_css = """
<style>
    .hidden-input {
        display: none;
    }
</style>
"""
st.markdown(hide_input_css, unsafe_allow_html=True)

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
       # Add reCAPTCHA and hidden input for the response
        st.markdown(recaptcha_html, unsafe_allow_html=True)
        recaptcha_response = st.text_input("recaptcha_response", type="default", value="", key="recaptcha_response_input")

        submit_button = st.form_submit_button(label='Submit')
        
with right_column:
    if submit_button:
        if recaptcha_response:
            # Verify the reCAPTCHA response
            recaptcha_verification = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": RECAPTCHA_SECRET_KEY,
                    "response": recaptcha_response
                }
            )
            recaptcha_result = recaptcha_verification.json()

            if recaptcha_result.get("success"):
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
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "You are a financial advisor who provides detailed and specific investment advice based on user profiles."},
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

                        Please include specific stock recommendations, bond recommendations, mutual funds/ETFs, asset allocation strategy, risk management, tax efficiency, and income generation strategies.
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
                st.error("reCAPTCHA verification failed. Please try again.")
    else:
        st.error("reCAPTCHA token missing. Please complete the CAPTCHA.")