
import streamlit as st
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz

st.set_page_config(page_title="AR Finder from Bank Statements")
st.title("🔍 AR Detection from Bank Statements (PDF only)")

# Load AR database directly from local file (included in repo)
@st.cache_data
def load_ar_database():
    return pd.read_excel("AR DATABASE DETAILS.xlsx")

ar_df = load_ar_database()
ar_names = ar_df["AR Name"].dropna().tolist()

# Upload bank statement PDF
pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])

def extract_pdf_lines(uploaded_pdf):
    lines = []
    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    return lines

if pdf_file:
    st.info("⏳ Reading and matching data...")
    transactions = extract_pdf_lines(pdf_file)

    results = []
    for line in transactions:
        for ar in ar_names:
            score = fuzz.partial_ratio(ar.lower(), line.lower())
            if score >= 85:
                match_email = ar_df[ar_df["AR Name"] == ar]["Email"].values[0]
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
