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

        if negative_amount_pattern.search(line_clean):
            continue

        if any(exclude_word in line_clean for exclude_word in ['minimum', 'balance', 'total', 'service fee', 'card summary', 'payment solutions', 'fee']):
            continue

        if positive_amount_pattern.search(line_clean) and any(keyword in line_clean for keyword in deposit_keywords):
            best_match = None
            highest_score = 0
            for ar in ar_names:
                # Improved matching using token_set_ratio
                score = fuzz.token_set_ratio(ar.lower(), line_clean)
                if score > highest_score and score >= 80:
                    highest_score = score
                    best_match = ar

            if best_match:
                match_row = ar_df[ar_df[ar_name_col] == best_match].iloc[0]
                results.append({
                    "Deposit Transaction": line.strip(),
                    "Matched AR": best_match,
                    "Email": match_row[ar_email_col] if pd.notna(match_row[ar_email_col]) else "",
                    "Country": match_row[ar_country_col] if pd.notna(match_row[ar_country_col]) else "",
                    "State": match_row[ar_state_col] if pd.notna(match_row[ar_state_col]) else ""
                })
            else:
                # Optional: clearly indicate no match (for debugging)
                results.append({
                    "Deposit Transaction": line.strip(),
                    "Matched AR": "NO MATCH FOUND",
                    "Email": "",
                    "Country": "",
                    "State": ""
                })

    if results:
        result_df = pd.DataFrame(results).drop_duplicates()
        st.success
