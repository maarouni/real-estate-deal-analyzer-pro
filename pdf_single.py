
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas

# ✅ Keys to skip (prevent duplicates like "10yr Cash Flow")
skip_keys = {"10Yr Cash Flow", "10yr Cash Flow"}

# Optional renaming of metric keys for user-friendly PDF display
rename_keys = {
    "roi_list": "Annual ROI % (by year)",
    "10yr Rents": "Annual Rents $ (by year)",
    "Final Year ROI (%)": "Final Year ROI (%)",
    "Multi-Year Cash Flow": "Multi-Year Cash Flow",
    "Annual ROI % (by year)": "Annual ROI % (by year)",
    "Annual Rents $ (by year)": "Annual Rents $ (by year)" # placeholder in case it's passed in future
}

# ✅ Order you want in the PDF
preferred_order = [
    "Cap Rate (%)",
    "Cash-on-Cash Return (%)",
    "Final Year ROI (%)",
    "First Year Cash Flow ($)",
    "Annual Cash Flow ($)",
    "Monthly Mortgage ($)",
    "Grade",
    "Multi-Year Cash Flow",  # Force this name only
    "Annual ROI % (by year)",
    "Annual Rents $ (by year)"
]

def format_display_value(key, value):
    """Format all numbers according to the agreed rules."""
    if isinstance(value, (float, int)):
            # Rule-based rounding
        if abs(value) >= 1:
            # round to nearest integer, no decimals
            return str(int(round(value)))
        elif abs(value) > 0:
            # keep up to 2 decimals for small fractional values
            return f"{value:.2f}"
        else:
            return "0"
    return str(value)

# ✅ Define AI Verdict function BEFORE generate_pdf

def parse_numeric(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0.0
def generate_ai_verdict(metrics: dict) -> tuple[str, str]:
    print("🗝️ Available metric keys:", list(metrics.keys()))

    #roi = parse_numeric(metrics.get("Final Year ROI (%)") or metrics.get("ROI (%)", 0))
    roi = parse_numeric(metrics.get("Final Year ROI (%)"))
    if roi == 0.0:
        roi = parse_numeric(metrics.get("ROI (%)", 0))
    #cash_flow = parse_numeric(metrics.get("Annual Cash Flow ($)", 0))
    coc_return = parse_numeric(metrics.get("Cash-on-Cash Return (%)", 0))

    # ✅ Use Multi-Year Cash Flow to sum total
    raw_cash_flow = metrics.get("Multi-Year Cash Flow", [])
    print("🧾 Raw cash flow data (before processing):", raw_cash_flow)

    #print("🧾 Raw cash flow data (before processing):", raw_cash_flow)  # Debug line

   # ✅ Step 1: Handle case where it's a comma-separated string
    if isinstance(raw_cash_flow, str):
        try:
            raw_cash_flow = [parse_numeric(x) for x in raw_cash_flow.split(",")]
        except:
            raw_cash_flow = []

    elif isinstance(raw_cash_flow, list):
        raw_cash_flow = [parse_numeric(x) for x in raw_cash_flow]
    else:
        raw_cash_flow = []

    cash_flow = sum(raw_cash_flow)

    print("🧾 Parsed cash flow list:", raw_cash_flow)
    print(f"🧪 Debug: ROI={roi}, CashFlow={cash_flow}, CoC Return={coc_return}")
    
    # Sample grading logic
    if roi > 200 and cash_flow > 20000 and coc_return >= 5:
        grade = "A"
        summary = "This is an A-grade investment with high returns and strong cash flow."
    elif roi > 100 and cash_flow > 10000 and coc_return >= 0:
        grade = "B"
        summary = "This is a B-grade investment with solid performance and good ROI."
    elif roi > 50 and cash_flow > 5000 and coc_return >= -5:
        grade = "C"
        summary = "This is a C-grade investment with modest returns."
    elif roi > 0 and cash_flow > 0 and coc_return >= 6:
        grade = "D"
        summary = "This is a D-grade investment with marginal upside potential."
    else:
        grade = "F"
        summary = "This is an F-grade rental with upside potential."

    return summary, grade

"""def generate_pdf(metrics, time_horizon, street_address=None, zip_code=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Title and Address
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 770, "Real Estate Investment Report")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"📍 Address: {street_address or 'N/A'}   ZIP: {zip_code or 'N/A'}")

    # Metrics
    p.drawString(50, 720, f"Time Horizon (Years): {time_horizon}")
    p.drawString(50, 700, f"IRR (%): {metrics.get('irr', 0):.2f}")
    p.drawString(50, 680, f"Equity Multiple: {metrics.get('equity_multiple', 0):.2f}")
    p.drawString(50, 660, f"Total Return: ${metrics.get('total_return', 0):,.2f}")
    p.drawString(50, 640, f"Cash-on-Cash Return (%): {metrics.get('cash_on_cash_return', 0):.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
"""

def generate_pdf(property_data, metrics, summary_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()


    # 📍 Add Street Address + ZIP
    address = property_data.get("street_address", "N/A")
    zip_code = property_data.get("zip_code", "N/A")
    elements.append(Paragraph(f"<b>📍 Property Address:</b> {address}   <b>ZIP:</b> {zip_code}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Title
    elements.append(Paragraph("Real Estate Evaluator Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # AI Verdict
    elements.append(Paragraph("<b><font color='green'> AI Verdict</font></b>", styles["Heading3"]))
    elements.append(Paragraph(summary_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # AI Disclaimer
    disclaimer_text = Paragraph(
        '<font size="9" color="darkblue">(AI-generated grade based on estimated ROI, cash flow, and risk factors. Informational only.)</font>',
        styles["Normal"]
    )
    elements.extend([disclaimer_text, Spacer(1, 12)])

    # Property & Loan Inputs
    elements.append(Paragraph("<b>🏠 Property & Loan Inputs</b>", styles["Heading3"]))
    inputs_data = [[k, str(v)] for k, v in property_data.items()]
    table_inputs = Table(inputs_data, colWidths=[200, 300])
    table_inputs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elements.append(table_inputs)
    elements.append(Spacer(1, 12))

    # Investment Metrics
    elements.append(Paragraph("<b>📊 Investment Metrics</b>", styles["Heading3"]))

    metrics_cleaned = []

    
    # ✅ Ordered rendering
    for key in preferred_order:
    
        if key in metrics and key not in skip_keys:
            value = metrics[key]
            if isinstance(value, list):
                grouped = [", ".join(format_display_value(key, val) for val in value[i:i+5])
                           for i in range(0, len(value), 5)
                ]
                wrapped = "<br/>".join(grouped)
                metrics_cleaned.append([key, Paragraph(wrapped, styles["Normal"])])
            elif isinstance(value, float):
                metrics_cleaned.append([key, format_display_value(key, value)])
            elif isinstance(value, str):
                if key == "AI Verdict":
                    continue  # Skip duplicate
                metrics_cleaned.append([key, Paragraph(value, styles["Normal"])])
            else:
                metrics_cleaned.append([key, value])   

    table_metrics = Table(metrics_cleaned, colWidths=[200, 350])  # wider cell
    table_metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table_metrics)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer 

# Alias for import compatibility
generate_pdf_report = generate_pdf
