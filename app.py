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

ar_df = load_ar_database()

# Column mapping (adjust based on your Excel)
ar_name_col = "AR NAME"
ar_email_col = "AR EMAILS"

# Additional columns (make sure these match your Excel columns)
ar_description_col = "AR Description"
ar_frequency_col = "AR Frequency"
ar_materiality_col = "AR Materiality"
ar_entity_name_col = "Name"
ar_entity_location_col = "Location"
ar_entity_industry_col = "Industry"
ar_entity_website_col = "Website"

pdf_file = st.file_uploader("Upload Bank Statement PDF", type=["pdf"])

if pdf_file:
    st.info("⏳ Processing PDF...")
    transactions = extract_pdf_lines(pdf_file)

    matched_ar = {}

    for line in transactions:
        for _, row in ar_df.iterrows():
            ar_name = row[ar_name_col]
            score = fuzz.partial_ratio(ar_name.lower(), line.lower())
            if score >= 85:
                if ar_name not in matched_ar:
                    matched_ar[ar_name] = {
                        "Section": "Deposits and Other Credits",
                        "AR Description": row.get(ar_description_col, "N/A"),
                        "AR Frequency": row.get(ar_frequency_col, "N/A"),
                        "AR Matching with AR Database": "Yes",
                        "Itemized AR Breakdown": [],
                        "AR Materiality": row.get(ar_materiality_col, "N/A"),
                        "AR Entity Details": f"{row.get(ar_entity_name_col, 'N/A')}, {row.get(ar_entity_location_col, 'N/A')}, {row.get(ar_entity_industry_col, 'N/A')}, {row.get(ar_entity_website_col, 'N/A')}"
                    }
                matched_ar[ar_name]["Itemized AR Breakdown"].append(f"• {line.strip()}")

    if matched_ar:
        report_data = []
        for ar, details in matched_ar.items():
            details["Itemized AR Breakdown"] = "\n".join(details["Itemized AR Breakdown"])
            report_data.append(details)

        result_df = pd.DataFrame(report_data)

        st.success(f"✅ {len(result_df)} ARs matched and organized!")
        st.dataframe(result_df)

        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Structured Report CSV", csv_data, "structured_ar_report.csv", "text/csv")
    else:
        st.warning("❌ No ARs matched in this bank statement.")
