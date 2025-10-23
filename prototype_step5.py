# prototype_step5.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Step 5 Prototype", layout="centered")

st.title("🧱 Step 5: Investment Enhancements Prototype")
st.markdown("Preview UI for capital improvements and depreciation before integrating with main app.")

# Sidebar Layout
st.sidebar.header("📌 Property Info (Dummy Inputs)")
property_value = st.sidebar.number_input("Property Value ($)", min_value=50000, max_value=2000000, step=5000, value=300000)
land_value = st.sidebar.number_input("Land Value ($)", min_value=0, max_value=property_value, step=1000, value=60000)

# =============================
# 🔧 Optional Enhancements & Adjustments
# =============================
with st.expander("🔧 Optional Enhancements & Adjustments", expanded=True):

    # 🏗️ Capital Improvements Tracker
    st.subheader("🏗️ Capital Improvements Tracker")
    st.caption("Use this to record upgrades like kitchen remodels, HVAC systems, or roof replacements.")

    # ✅ Pre-populated 1-row editable table with numeric Amount and text Description
    initial_data = pd.DataFrame({
        "Year": [""],
        "Amount ($)": [0.0],
        "Description": [""]
    })

    improvements_df = st.data_editor(
        initial_data,
        num_rows="dynamic",
        width="stretch",
        key="improvements_editor"
    )

    # ✅ Convert numeric safely
    if "Amount ($)" in improvements_df:
        try:
            improvements_df["Amount ($)"] = pd.to_numeric(improvements_df["Amount ($)"], errors="coerce").fillna(0)
        except Exception:
            pass

    total_improvement_cost = float(improvements_df["Amount ($)"].sum()) if not improvements_df.empty else 0.0
    st.success(f"📊 Total Capital Improvements: ${total_improvement_cost:,.2f}")

    # 💸 Depreciation Modeling
    st.subheader("💸 Depreciation Modeling (Residential)")
    apply_depr = st.checkbox("Apply 27.5-Year Residential Depreciation?", value=True)

    if apply_depr:
        depreciation_base = max(0, property_value - land_value)
        annual_depreciation = depreciation_base / 27.5 if depreciation_base > 0 else 0
        st.info(f"📉 Annual Depreciation: ${annual_depreciation:,.2f}")
    else:
        st.warning("📌 Depreciation not applied.")
        annual_depreciation = 0.0  # fallback for summary

# =============================
# 🧾 Summary Preview
# =============================
st.markdown("## 📋 Summary")

st.markdown(f"""
- **Total Capital Improvements:** ${total_improvement_cost:,.2f}  
- **Annual Depreciation (if applied):** ${annual_depreciation:,.2f}  
""")

# Optional: Simulated effect on net taxable income
if apply_depr:
    taxable_income = 20000  # Dummy income
    net_taxable = max(0, taxable_income - annual_depreciation)
    st.markdown(f"**💼 Net Taxable Income (based on $20K dummy income):** ${net_taxable:,.2f}")
