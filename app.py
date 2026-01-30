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

# Extra utilities (embeddings / export)
from scripts.build_vector_store import build_vector_store
from scripts.export_chroma import export_chroma_csv

# Import query functions (Week 7 - AI Engineer)
try:
    from query_resumes import answer_question, search_resumes
    QUERY_AVAILABLE = True
except Exception:
    QUERY_AVAILABLE = False

# Import matching functions (Week 8)
try:
    from match_resumes import match_top_candidates
    MATCHING_AVAILABLE = True
except Exception:
    MATCHING_AVAILABLE = False

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Analyze Resume", "⚙️ Pipeline Manager", "👥 Browse Candidates", "🔍 AI Search", "🎯 Job Matching"])


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
    render_pipeline_card("🚀 Run Complete Pipeline", "Execute all 3 steps: Extract → Structure → Embed", highlight=True)
    
    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("📄 Step 1/3: Extracting text from PDFs...")
            process_all_pdfs()
            progress_bar.progress(33)
            
            status_text.info("🤖 Step 2/3: Processing with AI...")
            section_all_resumes()
            progress_bar.progress(66)
            
            status_text.info("🧠 Step 3/3: Building embeddings...")
            build_vector_store()
            progress_bar.progress(100)
            
            status_text.success("✅ Pipeline complete! AI Search is ready.")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Pipeline error: {e}")

    # -------------------------------
    # Step 3: Build Embeddings for AI Search
    # -------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    render_pipeline_card("🧠 Step 3: Build Embeddings", "Create vector embeddings for AI-powered search (required for AI Search tab)")
    
    if st.button("🧠 Build Embeddings", key="build_embeddings", use_container_width=True):
        with st.spinner("🧠 Building embeddings (this may take a minute)..."):
            try:
                build_vector_store()
                st.success("✅ Embeddings built! AI Search is now ready.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    # -------------------------------
    # Export utility
    # -------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📤 Export Database to CSV"):
        include_emb = st.checkbox("Include embeddings in CSV (large file)", value=False)
        if st.button("📤 Export to CSV", key="export_db", use_container_width=True):
            with st.spinner("Exporting Chroma DB to CSV..."):
                try:
                    n = export_chroma_csv(include_embeddings=include_emb)
                    st.success(f"✅ Exported {n} rows to data/chroma_export.csv")
                    with open("data/chroma_export.csv", "rb") as fh:
                        st.download_button("Download CSV", fh, file_name="chroma_export.csv")
                except Exception as e:
                    st.error(f"Error exporting DB: {e}")


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
            search_term = st.text_input("🔍 Search candidates...", "", placeholder="Enter name or ID", key="candidate_search")
        
        # Track search changes to reset pagination
        if "last_search" not in st.session_state:
            st.session_state.last_search = ""
        if "browse_page" not in st.session_state:
            st.session_state.browse_page = 1
        
        # Reset to page 1 when search changes
        if search_term != st.session_state.last_search:
            st.session_state.browse_page = 1
            st.session_state.last_search = search_term
        
        # Filter files by ID (searches ALL candidates)
        search_term = search_term.strip()  # Remove leading/trailing whitespace
        if search_term:
            filtered_files = [f for f in structured_files if search_term.lower() in f.stem.lower()]
            if filtered_files:
                st.success(f"Found {len(filtered_files)} candidate(s) matching '{search_term}' (searching all {len(structured_files)} candidates)")
            else:
                st.warning(f"No candidates found matching '{search_term}' in {len(structured_files)} candidates")
        else:
            filtered_files = structured_files

        # ---------------------------------
        # Quick skill-based search (uses hybrid keyword + semantic)
        # ---------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        ai_query = st.text_input("🔎 Search by skills (e.g., 'Python', 'Java developer')", "", key="browse_skill_search")
        ai_k = st.slider("Top k results", min_value=1, max_value=10, value=5, key="browse_k_slider")

        if ai_query and st.button("🔍 Search Skills", key="ai_search"):
            if QUERY_AVAILABLE:
                try:
                    from query_resumes import search_resumes
                    with st.spinner("Searching candidates..."):
                        results = search_resumes(ai_query, n_results=ai_k)
                    
                    if not results:
                        st.info("No candidates found with those skills.")
                    else:
                        for r in results:
                            match_badge = "🎯 Exact Match" if r.get("match_type") == "keyword" else "🔍 Semantic Match"
                            keywords = r.get("matched_keywords", [])
                            
                            st.markdown(f"**Candidate {r['id']}** — {match_badge}")
                            if keywords:
                                st.markdown(f"*Matched: {', '.join(keywords)}*")
                            
                            # Show content preview
                            content = r.get("content", "")
                            if content:
                                st.write(content[:300] + "..." if len(content) > 300 else content)
                            
                            st.divider()
                except Exception as e:
                    st.error(f"Error searching: {e}")
            else:
                st.warning("AI Search not available. Run the pipeline first.")
        
        # Pagination
        col1, col2, col3 = st.columns([1, 2, 1])
        items_per_page = 5
        total_pages = max(1, (len(filtered_files) + items_per_page - 1) // items_per_page)
        
        # Ensure page is within valid range
        if st.session_state.browse_page > total_pages:
            st.session_state.browse_page = 1
        
        with col2:
            page = st.selectbox(
                "Page", 
                range(1, total_pages + 1), 
                index=st.session_state.browse_page - 1,
                key="browse_page_select",
                label_visibility="collapsed"
            )
            st.session_state.browse_page = page
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


# ============================================
# TAB 4: AI SEARCH (Week 7)
# ============================================
with tab4:
    render_section_header("🔍 Ask AI About Candidates")
    
    if not QUERY_AVAILABLE:
        st.warning("⚠️ Query system not available. Make sure ChromaDB embeddings are set up.")
    else:
        # Instructions
        st.markdown("""
        <div class="card">
            <h4>💡 What can you ask?</h4>
            <ul>
                <li>"Does any candidate know Python?"</li>
                <li>"Show me candidates with machine learning experience"</li>
                <li>"Who has worked at a startup?"</li>
                <li>"Find candidates with SQL and data analysis skills"</li>
                <li>"Which candidates have a Master's degree?"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Question input
        st.markdown("<br>", unsafe_allow_html=True)
        question = st.text_input(
            "❓ Ask a question about candidates:",
            placeholder="e.g., Does this resume mention Python?",
            key="ai_question"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            num_results = st.slider("Number of resumes to search", 3, 10, 5)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_btn = st.button("🚀 Ask AI", type="primary", use_container_width=True)
        
        # Handle search
        if search_btn and question:
            with st.spinner("🤖 AI is searching and analyzing resumes..."):
                try:
                    result = answer_question(question, n_results=num_results)
                    
                    # Display answer
                    render_section_header("📝 AI Answer")
                    st.markdown(f"""
                    <div class="card">
                        {result['answer']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display sources
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"**📚 Sources** ({result['num_results']} resumes analyzed)")
                    
                    for src in result["sources"]:
                        relevance_pct = int(src["score"] * 100)
                        match_type = src.get("match_type", "semantic")
                        matched_kw = src.get("matched_keywords", [])
                        
                        if matched_kw:
                            kw_str = ", ".join(matched_kw)
                            st.markdown(f"- **Candidate {src['id']}** - 🎯 Matched: **{kw_str}**")
                        else:
                            st.markdown(f"- **Candidate {src['id']}** - Relevance: {relevance_pct}%")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Collection" in error_msg:
                        st.error("❌ ChromaDB not set up yet! Run embed_resumes.py first.")
                    else:
                        st.error(f"❌ Error: {e}")
        
        elif search_btn and not question:
            st.warning("Please enter a question first.")


# ============================================
# TAB 5: JOB MATCHING (Week 8)
# ============================================
with tab5:
    render_section_header("🎯 Match Candidates to Job Description")
    
    if not MATCHING_AVAILABLE:
        st.warning("⚠️ Matching system not available. Check that match_resumes.py exists.")
    else:
        # Instructions
        st.markdown("""
        <div class="card">
            <h4>📋 How it works</h4>
            <ol>
                <li>Paste or type a job description below</li>
                <li>Select how many candidates to evaluate</li>
                <li>Click "Match Candidates" to get scored results</li>
            </ol>
            <p><strong>Each candidate gets:</strong> Score (0-100), Strengths, Gaps, and Reasoning</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Job description input
        job_description = st.text_area(
            "📝 Job Description",
            placeholder="""Paste the job description here. Example:

Senior Python Developer

Requirements:
- 5+ years Python experience
- Django or FastAPI experience
- Strong SQL skills
- REST API development

Nice to have:
- Machine learning experience
- Docker/Kubernetes
- Cloud experience (AWS/GCP)""",
            height=250,
            key="job_description"
        )
        
        # Options
        col1, col2 = st.columns(2)
        with col1:
            n_candidates = st.slider("Number of candidates to evaluate", 5, 30, 10, key="n_match_candidates")
        with col2:
            st.info(f"⏱️ Estimated time: ~{n_candidates * 2} seconds")
        
        # Match button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            match_btn = st.button("🎯 Match Candidates", type="primary", use_container_width=True)
        
        # Handle matching
        if match_btn and job_description.strip():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                progress_bar.progress(current / total)
                status_text.info(f"🔄 Analyzing candidate {current}/{total}...")
            
            with st.spinner("🤖 AI is analyzing candidates..."):
                try:
                    results = match_top_candidates(
                        job_description.strip(),
                        n_candidates=n_candidates,
                        progress_callback=update_progress
                    )
                    
                    progress_bar.progress(1.0)
                    status_text.success(f"✅ Analyzed {len(results)} candidates!")
                    
                    if results:
                        st.markdown("<br>", unsafe_allow_html=True)
                        render_section_header(f"📊 Top {len(results)} Candidates")
                        
                        # Results table
                        for i, r in enumerate(results, 1):
                            score = r["score"]
                            
                            # Color based on score
                            if score >= 75:
                                score_color = "#28a745"  # Green
                                badge = "🟢 Strong Match"
                            elif score >= 60:
                                score_color = "#ffc107"  # Yellow
                                badge = "🟡 Good Match"
                            elif score >= 40:
                                score_color = "#fd7e14"  # Orange
                                badge = "🟠 Partial Match"
                            else:
                                score_color = "#dc3545"  # Red
                                badge = "🔴 Weak Match"
                            
                            with st.expander(f"#{i} Candidate {r['candidate_id']} — **{score}/100** {badge}", expanded=(i <= 3)):
                                # Score bar
                                st.markdown(f"""
                                <div style="background: #e0e0e0; border-radius: 10px; height: 20px; margin-bottom: 1rem;">
                                    <div style="background: {score_color}; width: {score}%; height: 100%; border-radius: 10px;"></div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Summary
                                st.markdown(f"**📋 Summary:** {r['summary']}")
                                
                                # Strengths & Gaps in columns
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**✅ Strengths:**")
                                    if r['strengths']:
                                        for s in r['strengths'][:5]:
                                            st.markdown(f"- {s}")
                                    else:
                                        st.caption("None identified")
                                
                                with col2:
                                    st.markdown("**⚠️ Gaps:**")
                                    if r['gaps']:
                                        for g in r['gaps'][:5]:
                                            st.markdown(f"- {g}")
                                    else:
                                        st.caption("None identified")
                                
                                # Reasoning
                                st.markdown("**💭 Reasoning:**")
                                st.write(r['reasoning'])
                                
                                # Skills
                                if r.get('skills'):
                                    st.markdown("**🛠️ Skills:**")
                                    st.write(" • ".join(r['skills'][:15]))
                        
                        # Download results
                        st.markdown("<br>", unsafe_allow_html=True)
                        results_json = json.dumps(results, indent=2, ensure_ascii=False)
                        st.download_button(
                            "📥 Download Results (JSON)",
                            results_json,
                            file_name="matching_results.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    else:
                        st.warning("No candidates could be analyzed. Make sure the pipeline has been run.")
                        
                except Exception as e:
                    st.error(f"❌ Error during matching: {e}")
        
        elif match_btn and not job_description.strip():
            st.warning("Please enter a job description first.")
