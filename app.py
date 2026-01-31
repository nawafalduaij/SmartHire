"""
SmartHire - AI-Powered Recruitment Assistant
Main Streamlit Application
"""
import streamlit as st
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

# Import components
from components import (
    load_css, render_hero, render_sidebar,
    get_dataset_stats, get_directories, process_single_resume,
    render_tab_analyze, render_tab_pipeline, render_tab_browse,
    render_tab_ai_search, render_tab_matching
)

# Import pipeline functions
from pdf_extractor import process_all_pdfs
from section_resumes import process_all_txt as section_all_resumes
from scripts.build_vector_store import build_vector_store
from scripts.export_chroma import export_chroma_csv

# Import query functions (optional - may not be set up yet)
QUERY_ERROR = None
try:
    from query_resumes import answer_question, search_resumes
    QUERY_AVAILABLE = True
except Exception as e:
    answer_question, search_resumes = None, None
    QUERY_AVAILABLE = False
    QUERY_ERROR = str(e)

# Import matching functions (optional)
MATCHING_ERROR = None
try:
    from match_resumes import match_top_candidates
    MATCHING_AVAILABLE = True
except Exception as e:
    match_top_candidates = None
    MATCHING_AVAILABLE = False
    MATCHING_ERROR = str(e)

# ============================================
# SETUP
# ============================================
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

# Load styling and render layout
load_css()
stats = get_dataset_stats()
render_hero()
render_sidebar(stats)

# ============================================
# TABS
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Analyze Resume",
    "⚙️ Pipeline Manager", 
    "👥 Browse Candidates",
    "🔍 AI Search",
    "🎯 Job Matching"
])

with tab1:
    render_tab_analyze(dirs, process_single_resume)

with tab2:
    render_tab_pipeline(stats, process_all_pdfs, section_all_resumes, build_vector_store, export_chroma_csv)

with tab3:
    render_tab_browse(dirs, search_resumes, QUERY_AVAILABLE)

with tab4:
    render_tab_ai_search(answer_question, QUERY_AVAILABLE, QUERY_ERROR)

with tab5:
    render_tab_matching(match_top_candidates, MATCHING_AVAILABLE, MATCHING_ERROR)
