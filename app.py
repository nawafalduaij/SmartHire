"""
SmartHire - AI-Powered Recruitment Assistant
Main Streamlit Application
"""
import streamlit as st
import json
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

# Import components
from components import load_css, display_sections, render_sidebar, render_hero
from components.helpers import get_dataset_stats, process_single_resume, get_directories
from components.ui import render_section_header, render_upload_area, render_info_card, render_stat_card, render_pipeline_card

# Import pipeline functions
from pdf_extractor import process_all_pdfs
from section_resumes import process_all_txt as section_all_resumes

# Get directories
dirs = get_directories()

# Ensure directories exist
for dir_path in [dirs["raw"], dirs["text"], dirs["sectioned"], dirs["uploads"]]:
    dir_path.mkdir(parents=True, exist_ok=True)


# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="SmartHire - AI Recruitment", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load styling
load_css()

# Get stats
stats = get_dataset_stats()

# Render hero and sidebar
render_hero()
render_sidebar(stats)


# ============================================
# TABS
# ============================================
tab1, tab2, tab3 = st.tabs(["📄 Analyze Resume", "⚙️ Pipeline Manager", "👥 Browse Candidates"])


# ============================================
# TAB 1: ANALYZE RESUME
# ============================================
with tab1:
    render_section_header("📄 Upload & Analyze Resume")
    
    col_upload, col_info = st.columns([2, 1])
    
    with col_upload:
        render_upload_area()
        uploaded_file = st.file_uploader("Upload Resume", type=["pdf"], label_visibility="collapsed")
    
    with col_info:
        render_info_card()
    
    if uploaded_file is not None:
        # Save uploaded file
        save_path = dirs["uploads"] / uploaded_file.name
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")
        
        # Advanced options
        with st.expander("⚙️ Advanced Options", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                show_raw = st.checkbox("Show raw extracted text", value=False)
            with col2:
                show_clean = st.checkbox("Show cleaned text", value=False)
        
        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_btn = st.button("🚀 Analyze Resume with AI", type="primary", use_container_width=True)
        
        if analyze_btn:
            with st.spinner("🤖 AI is analyzing the resume..."):
                result = process_single_resume(save_path)
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                render_section_header("📊 Analysis Results")
                display_sections(result["sections"])
                
                if show_raw:
                    with st.expander("📄 Raw Extracted Text"):
                        st.text_area("Raw Text", result["raw_text"], height=200, label_visibility="collapsed")
                
                if show_clean:
                    with st.expander("🧹 Cleaned Text"):
                        st.text_area("Cleaned Text", result["clean_text"], height=200, label_visibility="collapsed")
                
                # Download button
                st.divider()
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    json_output = json.dumps(result["sections"], indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_output,
                        file_name=f"{save_path.stem}_structured.json",
                        mime="application/json",
                        use_container_width=True
                    )


# ============================================
# TAB 2: PIPELINE MANAGER
# ============================================
with tab2:
    render_section_header("⚙️ Data Processing Pipeline")
    
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        render_stat_card(stats["raw_pdfs"], "📁 Raw PDFs", "#667eea")
    with col2:
        render_stat_card(stats["extracted_text"], "📝 Extracted", "#28a745")
    with col3:
        render_stat_card(stats["sectioned_json"], "🤖 AI Processed", "#764ba2")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Pipeline steps
    col1, col2 = st.columns(2)
    
    with col1:
        render_pipeline_card("📄 Step 1: Extract Text", "Convert PDF files to plain text using pdfplumber")
        if st.button("▶️ Run Extraction", key="extract", use_container_width=True):
            with st.spinner("📄 Extracting text from PDFs..."):
                try:
                    process_all_pdfs()
                    st.success("✅ PDF extraction complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        render_pipeline_card("🤖 Step 2: AI Structuring", "Use LLM to extract structured resume data")
        if st.button("🤖 Run AI Processing", key="section", use_container_width=True):
            with st.spinner("🤖 Processing with AI (this may take a while)..."):
                try:
                    section_all_resumes()
                    st.success("✅ AI processing complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Full pipeline
    render_pipeline_card("🚀 Run Complete Pipeline", "Execute all steps in sequence", highlight=True)
    
    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("📄 Step 1/2: Extracting text from PDFs...")
            process_all_pdfs()
            progress_bar.progress(50)
            
            status_text.info("🤖 Step 2/2: Processing with AI...")
            section_all_resumes()
            progress_bar.progress(100)
            
            status_text.success("✅ Pipeline complete!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Pipeline error: {e}")


# ============================================
# TAB 3: BROWSE CANDIDATES
# ============================================
with tab3:
    render_section_header("👥 Candidate Database")
    
    structured_files = list(dirs["sectioned"].glob("*.json"))
    
    if not structured_files:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 3rem;">
            <h3>📭 No Candidates Yet</h3>
            <p>Run the processing pipeline to add resumes to the database.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Stats and search
        col1, col2 = st.columns([1, 2])
        with col1:
            render_stat_card(len(structured_files), "Total Candidates", "#667eea")
        with col2:
            search_term = st.text_input("🔍 Search candidates...", "", placeholder="Enter name or ID")
        
        # Filter files
        if search_term:
            filtered_files = [f for f in structured_files if search_term.lower() in f.stem.lower()]
        else:
            filtered_files = structured_files
        
        # Pagination
        col1, col2, col3 = st.columns([1, 2, 1])
        items_per_page = 5
        total_pages = max(1, (len(filtered_files) + items_per_page - 1) // items_per_page)
        with col2:
            page = st.selectbox("Page", range(1, total_pages + 1), index=0, label_visibility="collapsed")
        with col3:
            st.caption(f"Page {page} of {total_pages}")
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_files = filtered_files[start_idx:end_idx]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display candidates
        for file in page_files:
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                sections = data.get("sections", {})
                
                with st.expander(f"👤 Candidate {file.stem}"):
                    st.markdown(f"**📋 Summary:** {sections.get('summary', 'N/A')}")
                    
                    if sections.get("skills"):
                        st.markdown("**🛠️ Skills:**")
                        skills_display = " • ".join(sections.get("skills", []))
                        st.markdown(f'<p style="color: #667eea;">{skills_display}</p>', unsafe_allow_html=True)
                    
                    st.divider()
                    display_sections(sections)
                    
            except Exception as e:
                st.error(f"Error loading {file.name}: {e}")
