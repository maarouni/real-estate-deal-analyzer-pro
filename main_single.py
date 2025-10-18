
import streamlit as st
import os
from dotenv import load_dotenv
from calculations import calculate_metrics
from pdf_generator_single import generate_pdf
from pdf_generator_single import generate_ai_verdict
import matplotlib.pyplot as plt
from email.message import EmailMessage
import smtplib
import re

load_dotenv()

st.set_page_config(page_title="Single Property Evaluator", layout="centered")
st.title("🏡 Real Estate Deal Evaluator")
st.markdown("Analyze the investment potential of a single property.")

# Default password (can be overridden by .env)
APP_PASSWORD = os.getenv("APP_PASSWORD", "SmartInvest1!")

# Use session state to remember successful login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show password input only if not yet authenticated
if not st.session_state.authenticated:
    #st.title("🏠 Real Estate Deal Evaluator")
    password = st.text_input("🔒 Please enter access password", type="password")

    if password == APP_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()  # 🔁 Clear the password input and reload
    elif password:
        st.error("❌ Incorrect password. Please try again.")
    st.stop()  # 🔒 Block access until correct
    

# 📌 Property Information
st.sidebar.header("📌 Property Information")
street_address = st.sidebar.text_input("Street Address (optional)")
zip_code = st.sidebar.text_input("ZIP Code (optional)")
purchase_price = st.sidebar.number_input("Purchase Price ($)", min_value=10000, value=300000, step=1000)
monthly_rent = st.sidebar.number_input("Expected Monthly Rent ($)", min_value=0, value=2000, step=100)
monthly_expenses = st.sidebar.number_input("Monthly Expenses ($: property tax + insurance + miscellaneous)", min_value=0, value=300, step=50)

# 💰 Financing & Growth
st.sidebar.header("💰 Financing & Growth")
down_payment_pct = st.sidebar.slider("Down Payment (%)", 0, 100, 20)
interest_rate = st.sidebar.slider("Interest Rate (%)", 0.0, 15.0, 6.5)
loan_term = st.sidebar.number_input("Loan Term (years)", min_value=1, value=30)
vacancy_rate = st.sidebar.slider("Vacancy Rate (%)", 0, 100, 5)
appreciation_rate = st.sidebar.slider("Annual Appreciation Rate (%)", 0, 10, 3)
rent_growth_rate = st.sidebar.slider("Annual Rent Growth Rate (%)", 0, 10, 3)
time_horizon = st.sidebar.slider("🏁 Investment Time Horizon (Years)", 1, 30, 10)

# 🔢 Run Calculations
metrics = calculate_metrics(
    purchase_price, monthly_rent, monthly_expenses,
    down_payment_pct, interest_rate, loan_term,
    vacancy_rate, appreciation_rate, rent_growth_rate,
    time_horizon
)

# 🧾 Generate PDF
#pdf_bytes = generate_pdf(metrics, time_horizon, street_address, zip_code)
property_data = {
    "street_address": street_address,
    "zip_code": zip_code,
    "purchase_price": purchase_price,
    "monthly_rent": monthly_rent,
    "monthly_expenses": monthly_expenses,
    "down_payment_pct": down_payment_pct,
    "interest_rate": interest_rate,
    "loan_term": loan_term,
    "vacancy_rate": vacancy_rate,
    "appreciation_rate": appreciation_rate,
    "rent_growth_rate": rent_growth_rate,
    "time_horizon": time_horizon
}

summary_text, grade = generate_ai_verdict(metrics)
pdf_bytes = generate_pdf(property_data, metrics, summary_text)

# 📊 Display Long-Term Metrics
st.markdown("## 📉 Long-Term Metrics")
col1, col2 = st.columns(2)
col1.metric("IRR (%)", f"{metrics.get('irr (%)', 0):.2f}")
col2.metric("Equity Multiple", f"{metrics.get('equity_multiple', 0):.2f}")

# 📈 Multi-Year Cash Flow Projection
st.subheader("📈 Multi-Year Cash Flow Projection")
fig, ax = plt.subplots()
years = list(range(1, time_horizon + 1))
ax.plot(years, metrics["Multi-Year Cash Flow"], marker='o', label="Multi-Year Cash Flow ($)")
ax.plot(years, metrics["Annual Rents $ (by year)"], marker='s', linestyle='--', label="Projected Rent ($)")
ax.set_xlabel("Year")
ax.set_ylabel("Projected Cash Flow / Rent ($)")
ax.grid(True)
ax2 = ax.twinx()
ax2.plot(years, metrics["Annual ROI % (by year)"], color='green', marker='^', label="ROI (%)")
ax2.set_ylabel("ROI (%)", color='green')
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc="upper left")
ax.set_title("Multi - Year Projected Cash Flow & ROI")
st.pyplot(fig)

# 📘 Download User Manual
st.markdown("---")
try:
    with open("User_Manual_Investment_Metrics_Explained_Styled_Final.pdf", "rb") as f:
        st.download_button(
            label="📘 Download User Manual (PDF)",
            data=f,
            file_name="Investment_Metrics_User_Guide.pdf",
            mime="application/pdf"
        )
except FileNotFoundError:
    st.error("📄 User Manual PDF is missing from directory.")

# 📄 PDF Download Section
if pdf_bytes is not None:
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="real_estate_report.pdf",
        mime="application/pdf",
        key="download_pdf_unique"
    )
else:
    st.error("⚠️ PDF generation failed. Please check your input or logs.")

# ✉️ Email This Report Section
st.markdown("### 📨 Email This Report")
recipient_email = st.text_input("Enter email address to send the report", placeholder="you@example.com")
if st.button("Send Email Report") and recipient_email:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
        st.error("❌ Please enter a valid email address.")
        st.stop()
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Real Estate Evaluation Report"
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = recipient_email
        msg.set_content("Please find attached your real estate evaluation report.")
        pdf_bytes.seek(0)
        msg.add_attachment(pdf_bytes.read(), maintype='application', subtype='pdf', filename="real_estate_report.pdf")
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)
        st.success(f"✅ Report sent to {recipient_email}!")
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
