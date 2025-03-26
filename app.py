import streamlit as st
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz
import re

@st.cache_data
def load_ar_database():
    return pd.read_excel("AR_DATABASE_DETAILS.xlsx", engine='openpyxl')

def extract_pdf_lines(uploaded_pdf):
    lines = []
    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    return lines

# Load AR database
ar_df = load_ar_database()

# Display exact columns to verify correct names:
st.write("Excel Column Names:", ar_df.columns.tolist())

# Corrected Column names exactly as per your Excel file
ar_name_col = "AR NAME"
ar_email_col = "AR EMAILS"
ar_country_col = "country"
ar_state_col = "STATE"

if ar_name_col not in ar_df.columns or ar_email_col not in ar_df.columns:
    st.error("⚠️ Column names in your Excel file do not match. Check the names above and update them in the code.")
else:
    ar_names = ar_df[ar_name_col].dropna().tolist()

    # PDF upload section
    pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])
    
if pdf_file:
    st.info("⏳ Processing PDF...")
    transactions = extract_pdf_lines(pdf_file)

    results = []

    deposit_keywords = [
        'atm cash deposit', 'remote online deposit', 'online transfer from',
        'net setlmt', 'edi paymnt', 'adv credit', 'ach credit', 'wire transfer',
        'doordash', 'uber', 'grubhub', 'citizens', 'united first', 'fundbox'
    ]

    negative_amount_pattern = re.compile(r'(-\$\s?[\d,]+\.\d{2}|\(\$\s?[\d,]+\.\d{2}\))')
    positive_amount_pattern = re.compile(r'\$\s?[\d,]+\.\d{2}')

    for line in transactions:
        line_clean = line.replace(',', '').lower()

        # Skip negative amounts
        if negative_amount_pattern.search(line_clean):
            continue

        # Explicitly exclude non-deposit informational lines
        if any(exclude_word in line_clean for exclude_word in ['minimum', 'balance', 'total', 'service fee', 'card summary', 'payment solutions', 'fee']):
            continue

        # Check for positive amounts and deposit keywords explicitly
        if positive_amount_pattern.search(line_clean) and any(keyword in line_clean for keyword in deposit_keywords):
            matched = False  # Track if a transaction matched
            for ar in ar_names:
                score = fuzz.partial_ratio(ar.lower(), line_clean)
                if score >= 70:  # Lowered from 85 to 70 to catch minor variations
                    match_row = ar_df[ar_df[ar_name_col] == ar].iloc[0]
                    results.append({
                        "Deposit Transaction": line.strip(),
                        "Matched AR": ar,
                        "Email": match_row[ar_email_col],
                        "Country": match_row.get(ar_country_col, ""),
                        "State": match_row.get(ar_state_col, "")
                    })
                    matched = True

            # Optional debugging (comment out if not needed)
            if not matched:
                results.append({
                    "Deposit Transaction": line.strip(),
                    "Matched AR": "NO MATCH FOUND",
                    "Email": "",
                    "Country": "",
                    "State": ""
                })

    if results:
        result_df = pd.DataFrame(results).drop_duplicates()
        st.success(f"✅ {len(result_df)} deposit transactions identified (including unmatched for debugging)!")
        st.dataframe(result_df)

        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Matched Deposits CSV", csv_data, "matched_ar_deposits.csv", "text/csv")
    else:
        st.warning("❌ No deposit transactions found in this bank statement.")
