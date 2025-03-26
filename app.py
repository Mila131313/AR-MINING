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

        # Regex pattern to extract amounts ($1,234.56 or -$1,234.56)
        amount_pattern = re.compile(r'(-?)\$\s?[\d,]+\.\d{2}')

        for line in transactions:
            amount_match = amount_pattern.search(line.replace(',', ''))
            if amount_match:
                is_negative = amount_match.group(1) == '-'

                # ONLY Deposits (positive amounts)
                if not is_negative:
                    line_lower = line.lower()
                    for ar in ar_names:
                        score = fuzz.partial_ratio(ar.lower(), line_lower)
                        if score >= 85:
                            match_row = ar_df[ar_df[ar_name_col] == ar].iloc[0]
                            results.append({
                                "Deposit Transaction": line.strip(),
                                "Matched AR": ar,
                                "Email": match_row[ar_email_col],
                                "Country": match_row.get(ar_country_col, ""),
                                "State": match_row.get(ar_state_col, "")
                            })

        if results:
            result_df = pd.DataFrame(results)
            st.success(f"✅ {len(result_df)} matches found!")
            st.dataframe(result_df)

            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results as CSV", csv_data, "matched_ar_results.csv", "text/csv")
        else:
            st.warning("❌ No ARs matched in this bank statement.")
