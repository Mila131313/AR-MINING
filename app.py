import streamlit as st
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz

@st.cache_data
def load_ar_database():
    return pd.read_excel("AR_DATABASE_DETAILS.xlsx", engine='openpyxl')

def extract_transactions(uploaded_pdf):
    transactions = []
    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                transactions.extend(text.split("\n"))
    return transactions

ar_df = load_ar_database()

pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])

if pdf_file:
    st.info("⏳ Processing PDF...")
    transactions = extract_transactions(pdf_file)

    results = []

    for _, ar_row in ar_df.iterrows():
        matched_transactions = []
        for line in transactions:
            if fuzz.partial_ratio(ar_row["AR NAME"].lower(), line.lower()) >= 85:
                matched_transactions.append(line.strip())

        results.append({
            "Section": "Deposits and Other Credits",
            "AR Description": ar_row.get("AR Description", "N/A"),
            "AR Frequency": ar_row.get("AR Frequency", "N/A"),
            "AR Matching": "Yes" if matched_transactions else "No",
            "Itemized AR Breakdown": "\n".join(f"• {item}" for item in matched_transactions) if matched_transactions else "-",
            "AR Materiality": ar_row.get("AR Materiality", "N/A"),
            "AR Entity Details": f"Name: {ar_row.get('Name', 'N/A')}, Location: {ar_row.get('Location', 'N/A')}, Industry: {ar_row.get('Industry', 'N/A')}, Website: {ar_row.get('Website', 'N/A')}"
        })

    result_df = pd.DataFrame(results)
    st.success(f"✅ Report generated with {len(result_df)} AR records!")
    st.dataframe(result_df)

    csv_data = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Organized Report as CSV", csv_data, "organized_ar_report.csv", "text/csv")
