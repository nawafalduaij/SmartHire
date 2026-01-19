import streamlit as st
from utils import extract_text_from_pdf

st.set_page_config(page_title="SmartHire MVP")
st.title("SmartHire: AI Recruiter")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file is not None:
    st.write("File Uploaded")
    text = extract_text_from_pdf(uploaded_file)
    with st.expander("View Content"):
        st.write(text)