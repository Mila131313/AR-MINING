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

    deposit_results = []
    negative_amount_pattern = re.compile(r'(-\$\s?[\d,]+\.\d{2}|\(\$\s?[\d,]+\.\d{2}\))')
    positive_amount_pattern = re.compile(r'\$\s?[\d,]+\.\d{2}')

    # Simplified deposit detection
    deposit_patterns = [
        'atm cash deposit', 'remote online deposit', 'online transfer from', 'fee reversal',
        'net setlmt', 'edi paymnt', 'adv credit', 'wire transfer', 'ach credit',
        'orig co name', 'deposit'
    ]

    for line in transactions:
        line_clean = line.replace(',', '').lower()

        # Explicitly skip negative amounts
        if negative_amount_pattern.search(line_clean):
            continue

        # Explicitly skip non-transactional informational lines
        if any(x in line_clean for x in ['minimum', 'ending balance', 'lowest daily', 'average balance', 'monthly service fee']):
            continue

        # Check explicitly for deposit patterns and positive amounts
        if positive_amount_pattern.search(line_clean) and any(keyword in line_clean for keyword in deposit_patterns):
            deposit_results.append({"Deposit Transaction": line.strip()})

    if deposit_results:
        deposit_df = pd.DataFrame(deposit_results).drop_duplicates()
        st.success(f"✅ {len(deposit_df)} deposit transactions identified!")
        st.dataframe(deposit_df)

        csv_data = deposit_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Deposit Transactions CSV", csv_data, "deposit_transactions.csv", "text/csv")
    else:
        st.warning("❌ No deposit transactions found in this bank statement.")
