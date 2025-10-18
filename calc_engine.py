from scipy.optimize import newton
import numpy as np
import numpy_financial as npf

def robust_irr(cash_flows, guess=0.1):
    def npv(rate):
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
    try:
        irr_solution = newton(npv, guess)
        return round(irr_solution * 100, 2)
    except Exception as e:
        print(f"IRR calculation failed: {e}")
        return 0

def calculate_metrics(purchase_price, monthly_rent, down_payment_pct, interest_rate, loan_term,
                      monthly_expenses, vacancy_rate, appreciation_rate, rent_growth_rate, time_horizon):
    
    loan_amount = purchase_price * (1 - down_payment_pct / 100)
    monthly_interest_rate = interest_rate / 100 / 12
    number_of_payments = loan_term * 12

    if monthly_interest_rate > 0:
        monthly_mortgage = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments) / \
                           ((1 + monthly_interest_rate) ** number_of_payments - 1)
    else:
        monthly_mortgage = loan_amount / number_of_payments

    effective_rent = monthly_rent * (1 - vacancy_rate / 100)
    annual_rent = effective_rent * 12
    annual_expenses = monthly_expenses * 12
    annual_mortgage = monthly_mortgage * 12
    annual_cash_flow = annual_rent - annual_expenses - annual_mortgage

    cap_rate = (annual_rent - annual_expenses) / purchase_price * 100
    coc_return = annual_cash_flow / (purchase_price * down_payment_pct / 100) * 100

    # --- Build multi-year cash flow ---
    cash_flows = []
    rents = []
    annual_cash_flows = []
    current_rent = monthly_rent

    for year in range(1, time_horizon + 1):
        effective_rent = current_rent * (1 - vacancy_rate / 100)
        annual_rent = effective_rent * 12
        annual_cash_flow = annual_rent - annual_expenses - annual_mortgage
        cash_flows.append(round(annual_cash_flow, 2))
        annual_cash_flows.append(round(annual_cash_flow, 2))
        rents.append(round(current_rent, 2))
        current_rent *= (1 + rent_growth_rate / 100)

    # --- IRR & Equity Multiple ---
    initial_investment = purchase_price * down_payment_pct / 100
    irr_cash_flows = [-initial_investment] + cash_flows
    irr = robust_irr(irr_cash_flows)

    total_cash_received = sum(cash_flows)
    equity_multiple = round(total_cash_received / initial_investment, 2) if initial_investment != 0 else 0

    # --- ROI per year ---
    appreciation_value = purchase_price * ((1 + appreciation_rate / 100) ** time_horizon - 1)
    down_payment_amount = purchase_price * (down_payment_pct / 100)

    roi_list = []
    for i in range(time_horizon):
        cumulative_return = sum(annual_cash_flows[:i + 1]) + appreciation_value * ((i + 1) / time_horizon)
        roi = (cumulative_return / down_payment_amount) * 100 if down_payment_amount != 0 else 0
        roi_list.append(round(roi, 2))

    # --- Grade Logic ---
    if coc_return >= 15:
        grade = "A"
    elif coc_return >= 12:
        grade = "B"
    elif coc_return >= 9:
        grade = "C"
    elif coc_return >= 6:
        grade = "D"
    else:
        grade = "F"

    # --- Final Return Dictionary ---
    return {
        "Cap Rate (%)": round(cap_rate, 2),
        "Cash-on-Cash Return (%)": round(coc_return, 2),
        "Final Year ROI (%)": round(roi_list[-1], 2),
        "First Year Cash Flow ($)": round(annual_cash_flows[0], 2),
        "Monthly Mortgage ($)": round(monthly_mortgage, 2),
        "Grade": grade,
        "10yr Cash Flow": annual_cash_flows,
        "Multi-Year Cash Flow": [round(x, 2) for x in annual_cash_flows],
        "Annual ROI % (by year)": roi_list,
        "Annual Rents $ (by year)": rents,
        "irr (%)": irr,
        "equity_multiple": equity_multiple
    }
