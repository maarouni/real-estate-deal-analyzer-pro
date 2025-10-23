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

def calculate_metrics(purchase_price, monthly_rent, down_payment_pct, mortgage_rate, mortgage_term,
                      monthly_expenses, vacancy_rate, appreciation_rate, rent_growth_rate, time_horizon):

    # ---- Loan basics
    down_payment_amount = purchase_price * (down_payment_pct / 100.0)
    loan_amount = purchase_price - down_payment_amount
    monthly_rate = (mortgage_rate / 100.0) / 12.0
    n_payments = int(mortgage_term * 12)

    # ---- Monthly mortgage payment (always positive dollars)
    if n_payments <= 0:
        monthly_mortgage_payment = 0.0
    elif monthly_rate > 0:
        # numpy_financial.pmt returns a negative number (cash outflow); take abs for display/math
        monthly_mortgage_payment = abs(npf.pmt(monthly_rate, n_payments, loan_amount))
    else:
        monthly_mortgage_payment = loan_amount / n_payments

    # ---- Year-1 flows (for cap rate / CoC / first-year cash flow)
    effective_monthly_rent = monthly_rent * (1 - vacancy_rate / 100.0)
    annual_rent = effective_monthly_rent * 12.0
    annual_expenses = monthly_expenses * 12.0
    annual_mortgage = monthly_mortgage_payment * 12.0

    annual_cash_flow = annual_rent - annual_expenses - annual_mortgage  # should be ~ -$1.1k in your example

    # ---- Metrics
    cap_rate = ((annual_rent - annual_expenses) / purchase_price) * 100.0 if purchase_price else 0.0
    coc_return = (annual_cash_flow / down_payment_amount) * 100.0 if down_payment_amount else 0.0

    # ---- Multi-year projections (rent growth only; expenses & mortgage held flat)
    cash_flows = []
    rents = []
    current_monthly_rent = monthly_rent
    for year in range(1, time_horizon + 1):
        eff_rent_mo = current_monthly_rent * (1 - vacancy_rate / 100.0)
        year_rent = eff_rent_mo * 12.0
        year_cash_flow = year_rent - annual_expenses - annual_mortgage
        cash_flows.append(round(year_cash_flow, 2))
        rents.append(round(current_monthly_rent * 12.0, 2))  # track annual rent dollars, optional
        current_monthly_rent *= (1 + rent_growth_rate / 100.0)

    print(f"[DEBUG] appreciation_rate={appreciation_rate}, time_horizon={time_horizon}, cash_flows={cash_flows[:3]} ...")

    # ---- IRR & Equity Multiple (dual-solver, operational + total) ----
    def safe_irr(cashflows):
        """Try npf.irr first; fallback to Newton if it fails."""
        try:
            val = npf.irr(cashflows)
            if val is None or np.isnan(val):
                raise ValueError("npf.irr failed")
            return round(val * 100.0, 2)
        except Exception:
            return robust_irr(cashflows)

    # --- Operational IRR (based on annual cash flows only) ---
    irr_operational = safe_irr([-down_payment_amount] + cash_flows)

    # --- Total IRR (adds terminal sale / appreciation value) ---
    sale_value = purchase_price * ((1 + appreciation_rate / 100.0) ** time_horizon)
    cash_flows_total = cash_flows.copy()
    if cash_flows_total:
        cash_flows_total[-1] += sale_value
    irr_total = safe_irr([-down_payment_amount] + cash_flows_total)

    # --- Equity Multiple (total case) ---
    total_cash_received = sum(cash_flows_total)
    equity_multiple = (
        round(total_cash_received / down_payment_amount, 2)
        if down_payment_amount
        else 0.0
    )


    # ---- ROI by year (simple heuristic including linearized appreciation)
    appreciation_value_total = purchase_price * ((1 + appreciation_rate / 100.0) ** time_horizon - 1)
    roi_list = []
    cum_cf = 0.0
    for i in range(time_horizon):
        cum_cf += cash_flows[i]
        # spread total appreciation evenly across years for a simple trend (same as your prior intent)
        linearized_app = appreciation_value_total * ((i + 1) / time_horizon)
        roi = ((cum_cf + linearized_app) / down_payment_amount) * 100.0 if down_payment_amount else 0.0
        roi_list.append(round(roi, 2))

    # ---- Grade (unchanged)
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

    return {
        "Cap Rate (%)": round(cap_rate, 2),
        "Cash-on-Cash Return (%)": round(coc_return, 2),
        "Final Year ROI (%)": round(roi_list[-1], 2) if roi_list else 0,
        "First Year Cash Flow ($)": round(cash_flows[0], 2) if cash_flows else 0,
        "Monthly Mortgage ($)": round(monthly_mortgage_payment, 2),
        "Grade": grade,
        "10yr Cash Flow": cash_flows,  # kept for back-compat
        "Multi-Year Cash Flow": [round(x, 2) for x in cash_flows],
        "Annual ROI % (by year)": roi_list,
        # If you want annual rent dollars (not monthly), keep as below; otherwise store monthly series
        "Annual Rents $ (by year)": rents,
        "irr (%)": irr_total,  # backward compatibility
        "IRR (Operational) (%)": irr_operational,
        "IRR (Total incl. Sale) (%)": irr_total,
        "equity_multiple": equity_multiple
    }
