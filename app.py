import streamlit as st
import os
import sys
import json
from pathlib import Path

# Add scripts folder to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import functions from scripts
from pdf_extractor import extract_text_from_pdf as extract_pdf_pdfplumber, process_all_pdfs
from clean_text_to_json import clean_text, process_all_txt_files
from build_sections import build_sections, process_files as build_all_sections
from inspect_sections import inspect_sections

# --- Directory Setup ---
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "fake_resumes"
PROCESSED_TEXT_DIR = DATA_DIR / "processed" / "resumes_text"
PROCESSED_CLEAN_DIR = DATA_DIR / "processed" / "resumes_clean"
PROCESSED_STRUCTURED_DIR = DATA_DIR / "processed" / "resumes_structured"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure directories exist
for dir_path in [RAW_DIR, PROCESSED_TEXT_DIR, PROCESSED_CLEAN_DIR, PROCESSED_STRUCTURED_DIR, UPLOADS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# --- Helper Functions ---
def process_single_resume(pdf_path: Path) -> dict:
    """
    Full pipeline for a single resume:
    1. Extract text from PDF
    2. Clean the text
    3. Build structured sections
    """
    # Step 1: Extract text from PDF
    raw_text = extract_pdf_pdfplumber(pdf_path)
    
    if not raw_text.strip():
        return {"error": "Could not extract text from PDF"}
    
    # Step 2: Clean the text
    cleaned_text = clean_text(raw_text)
    
    # Step 3: Build sections
    sections = build_sections(cleaned_text)
    
    return {
        "filename": pdf_path.name,
        "raw_text": raw_text,
        "clean_text": cleaned_text,
        "sections": sections
    }


def get_dataset_stats() -> dict:
    """Get statistics about the current dataset"""
    raw_pdfs = list(RAW_DIR.glob("*.pdf"))
    text_files = list(PROCESSED_TEXT_DIR.glob("*.txt"))
    clean_files = list(PROCESSED_CLEAN_DIR.glob("*.json"))
    structured_files = list(PROCESSED_STRUCTURED_DIR.glob("*.json"))
    
    return {
        "raw_pdfs": len(raw_pdfs),
        "extracted_text": len(text_files),
        "cleaned_json": len(clean_files),
        "structured_json": len(structured_files)
    }


def display_sections(sections: dict):
    """Display resume sections in a nice format"""
    section_icons = {
        "summary": "📋",
        "experience": "💼",
        "education": "🎓",
        "skills": "🛠️",
        "certifications": "📜",
        "other": "📄"
    }
    
    for section_name, content in sections.items():
        if content:
            icon = section_icons.get(section_name, "📄")
            with st.expander(f"{icon} {section_name.title()}", expanded=(section_name in ["summary", "skills"])):
                st.write(content)


# --- 1. Page Config ---
st.set_page_config(page_title="SmartHire - AI Recruitment", layout="wide")

# --- 2. Title & Sidebar ---
st.title("SmartHire: Intelligent Recruitment Assistant")
st.sidebar.header("Control Panel")

# Dataset stats in sidebar
stats = get_dataset_stats()
st.sidebar.subheader("Dataset Statistics")
st.sidebar.metric("Raw PDFs", stats["raw_pdfs"])
st.sidebar.metric("Extracted Text", stats["extracted_text"])
st.sidebar.metric("Cleaned JSON", stats["cleaned_json"])
st.sidebar.metric("Structured JSON", stats["structured_json"])

st.sidebar.divider()
st.sidebar.info("System Status: Online 🟢")

# --- 3. The Tabs ---
tab1, tab2, tab3 = st.tabs(["📄 Candidate Analysis", "🗄️ Dataset Manager", "🔍 Browse Resumes"])

# --- TAB 1: Single Resume Analysis ---
with tab1:
    st.header("Analyze a Resume")
    st.write("Upload a PDF resume to extract and analyze its content.")
    
    uploaded_file = st.file_uploader("Upload Candidate Resume (PDF)", type=["pdf"])
    
    if uploaded_file is not None:
        # Save uploaded file
        save_path = UPLOADS_DIR / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # Analysis options
        col1, col2 = st.columns(2)
        with col1:
            show_raw = st.checkbox("Show raw extracted text", value=False)
        with col2:
            show_clean = st.checkbox("Show cleaned text", value=False)
        
        # The Action Button
        if st.button("🚀 Extract & Analyze Resume", type="primary"):
            with st.spinner("SmartHire is processing the resume..."):
                result = process_single_resume(save_path)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("📊 Structured Resume Data")
                display_sections(result["sections"])
                
                # Optional: Show raw text
                if show_raw:
                    st.subheader("Raw Extracted Text")
                    st.text_area("Raw Text", result["raw_text"], height=200)
                
                # Optional: Show cleaned text
                if show_clean:
                    st.subheader("Cleaned Text")
                    st.text_area("Cleaned Text", result["clean_text"], height=200)
                
                # Download option
                st.divider()
                json_output = json.dumps(result["sections"], indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download Structured Data (JSON)",
                    data=json_output,
                    file_name=f"{save_path.stem}_structured.json",
                    mime="application/json"
                )

# --- TAB 2: Dataset Manager (Batch Processing) ---
with tab2:
    st.header("Dataset Management")
    st.write("Run the full data processing pipeline on the entire dataset.")
    
    # Show current stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Raw PDFs", stats["raw_pdfs"])
    with col2:
        st.metric("📝 Text Files", stats["extracted_text"])
    with col3:
        st.metric("🧹 Clean JSON", stats["cleaned_json"])
    with col4:
        st.metric("📊 Structured", stats["structured_json"])
    
    st.divider()
    
    # Pipeline steps
    st.subheader("🔧 Processing Pipeline")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Step 1: Extract Text**")
        st.caption("Convert PDFs to plain text files")
        if st.button("▶️ Run PDF Extraction", key="extract"):
            with st.spinner("Extracting text from PDFs..."):
                try:
                    process_all_pdfs()
                    st.success("✅ PDF extraction complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        st.write("**Step 2: Clean Text**")
        st.caption("Clean and normalize text files")
        if st.button("▶️ Run Text Cleaning", key="clean"):
            with st.spinner("Cleaning text files..."):
                try:
                    process_all_txt_files()
                    st.success("✅ Text cleaning complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col3:
        st.write("**Step 3: Build Sections**")
        st.caption("Extract resume sections")
        if st.button("▶️ Run Section Builder", key="sections"):
            with st.spinner("Building resume sections..."):
                try:
                    build_all_sections()
                    st.success("✅ Section building complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.divider()
    
    # Run full pipeline
    st.subheader("🚀 Full Pipeline")
    if st.button("▶️ Run Complete Pipeline", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Step 1/3: Extracting text from PDFs...")
            process_all_pdfs()
            progress_bar.progress(33)
            
            status_text.text("Step 2/3: Cleaning text files...")
            process_all_txt_files()
            progress_bar.progress(66)
            
            status_text.text("Step 3/3: Building resume sections...")
            build_all_sections()
            progress_bar.progress(100)
            
            status_text.text("✅ Pipeline complete!")
            st.success("All processing steps completed successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline error: {e}")

# --- TAB 3: Browse Processed Resumes ---
with tab3:
    st.header("Browse Processed Resumes")
    
    structured_files = list(PROCESSED_STRUCTURED_DIR.glob("*.json"))
    
    if not structured_files:
        st.warning("No processed resumes found. Run the pipeline in Dataset Manager first.")
    else:
        st.write(f"Found **{len(structured_files)}** processed resumes")
        
        # Search/filter
        search_term = st.text_input("🔍 Search by filename", "")
        
        # Filter files
        if search_term:
            filtered_files = [f for f in structured_files if search_term.lower() in f.stem.lower()]
        else:
            filtered_files = structured_files
        
        # Pagination
        items_per_page = 10
        total_pages = max(1, (len(filtered_files) + items_per_page - 1) // items_per_page)
        page = st.selectbox("Page", range(1, total_pages + 1), index=0)
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_files = filtered_files[start_idx:end_idx]
        
        # Display resumes
        for file in page_files:
            with st.expander(f"📄 {file.stem}"):
                try:
                    data = json.loads(file.read_text(encoding="utf-8"))
                    sections = data.get("sections", {})
                    display_sections(sections)
                except Exception as e:
                    st.error(f"Error loading file: {e}")