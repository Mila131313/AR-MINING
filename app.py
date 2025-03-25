import streamlit as st
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz

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

# Ensure these exactly match your Excel columns!
ar_name_col = "AR Name"
ar_email_col = "AR Email"
ar_country_col = "AR Country"
ar_state_col = "AR State"

if ar_name_col not in ar_df.columns or email_col not in ar_df.columns:
    st.error("⚠️ Column names in your Excel file do not match 'AR Name' or 'Email'. Check the names above and update them in the code.")
else:
    ar_names = ar_df[ar_name_col].dropna().tolist()

    # PDF upload section
    pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])

    if pdf_file:
        st.info("⏳ Processing PDF...")
        transactions = extract_pdf_lines(pdf_file)

        results = []
        for line in transactions:
            for ar in ar_s:
                score = fuzz.partial_ratio(ar.lower(), line.lower())
                if score >= 85:
                    match_email = ar_df[ar_df[ar__col] == ar][email_col].values[0]
                    results.append({
                        "Transaction": line.strip(),
                        "Matched AR": ar,
                        "Email": match_email
                    })

        if results:
            result_df = pd.DataFrame(results)
            st.success(f"✅ {len(result_df)} matches found!")
            st.dataframe(result_df)

            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results as CSV", csv_data, "matched_ar_results.csv", "text/csv")
        else:
            st.warning("❌ No ARs matched in this bank statement.")
