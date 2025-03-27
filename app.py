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
st.write("Excel Column Names:", ar_df.columns.tolist())

ar_name_col = "AR Name"
ar_email_col = "AR Email"

if ar_name_col not in ar_df.columns or ar_email_col not in ar_df.columns:
    st.error("⚠️ Column names in your Excel file do not match. Check the names above and update them in the code.")
else:
    ar_names = ar_df[ar_name_col].dropna().tolist()
    pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])

    if pdf_file:
        st.info("⏳ Processing PDF...")
        transactions = extract_pdf_lines(pdf_file)
        results = []

        # Only pattern checks
        negative_amount_pattern = re.compile(r'(-\$\s?[\d,]+\.\d{2}|\(\$\s?[\d,]+\.\d{2}\))')
        positive_amount_pattern = re.compile(r'\$\s?[\d,]+\.\d{2}')

        for line in transactions:
            line_clean = line.replace(',', '').lower()

            if negative_amount_pattern.search(line_clean):
                continue

            if any(exclude_word in line_clean for exclude_word in ['minimum', 'balance', 'total', 'service fee', 'card summary', 'payment solutions', 'fee']):
                continue

            if positive_amount_pattern.search(line_clean):
                matched_ars = []

                for ar in ar_names:
                    score = fuzz.token_set_ratio(ar.lower(), line_clean)
                    if score >= 50:
                        matched_ars.append((ar, score))

                matched_ars.sort(key=lambda x: x[1], reverse=True)

                if matched_ars:
                    top_ar, confidence = matched_ars[0]
                    match_row = ar_df[ar_df[ar_name_col] == top_ar].iloc[0]
                    results.append({
                        "Deposit Transaction": line.strip(),
                        "Matched AR": top_ar,
                        "Match Confidence (%)": confidence,
                        "Email": match_row.get(ar_email_col, ""),   

                    })
                else:
               results.append({
                "Deposit Transaction": line.strip(),
                "Matched AR": top_ar,
                "Match Confidence (%)": confidence,
                "Email": match_row.get(ar_email_col, "")
               })

        if results:
            result_df = pd.DataFrame(results).drop_duplicates()
            show_unmatched = st.checkbox("Show unmatched deposit lines", value=False)
            if not show_unmatched:
                result_df = result_df[result_df["Matched AR"] != "NO MATCH FOUND"]

            st.success(f"✅ {len(result_df)} matched deposit transactions identified!", icon="✅")
            st.dataframe(result_df)

            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Matched Deposits CSV", csv_data, "matched_ar_deposits.csv", "text/csv")
        else:
            st.warning("❌ No deposit transactions found in this bank statement.")
