"""
SmartHire - Tab Components
Each tab's content as a reusable function
"""
import base64
import json
import streamlit as st

from .ui import (
    render_section_header, render_upload_area, render_info_card,
    render_stat_card, render_pipeline_card, display_sections,
    render_empty_state, render_instructions_card, render_candidate_result
)
from .helpers import get_candidate_pdf_path

# st.dialog (1.46+) or st.experimental_dialog (1.36+) for pop-up PDF viewer
_dialog_decorator = getattr(st, "dialog", getattr(st, "experimental_dialog", None))


def _render_pdf_content(cid: str, dirs: dict, session_key: str, close_key: str):
    """Render PDF iframe and Close button (used in modal or inline)."""
    pdf_path = get_candidate_pdf_path(dirs, cid)
    if not pdf_path:
        st.warning("PDF not found.")
        if st.button("Close", key=close_key):
            if session_key in st.session_state:
                del st.session_state[session_key]
            st.rerun()
        return
    try:
        b64 = base64.b64encode(pdf_path.read_bytes()).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="80vh" style="min-height: 600px; border: none;"></iframe>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.caption("PDF too large to display.")
    if st.button("Close", key=close_key):
        if session_key in st.session_state:
            del st.session_state[session_key]
        st.rerun()


if _dialog_decorator:
    @_dialog_decorator("View PDF", width="large")
    def _pdf_modal(cid: str, dirs: dict, session_key: str):
        _render_pdf_content(cid, dirs, session_key, f"close_modal_{session_key}")
else:
    def _pdf_modal(cid: str, dirs: dict, session_key: str):
        """Fallback: no-op when st.dialog not available (use inline expander at call site)."""
        pass


def render_tab_analyze(dirs: dict, process_single_resume):
    """Tab 1: Upload & Analyze Resume (supports multiple PDFs)"""
    render_section_header("Upload & Analyze Resume")
    
    col_upload, col_info = st.columns([2, 1])
    
    with col_upload:
        render_upload_area()
        uploaded_files = st.file_uploader(
            "Upload Resumes",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    
    with col_info:
        render_info_card()
    
    if uploaded_files:
        # Save all uploaded files
        save_paths = []
        for uf in uploaded_files:
            save_path = dirs["uploads"] / uf.name
            with open(save_path, "wb") as f:
                f.write(uf.getbuffer())
            save_paths.append(save_path)
        
        n = len(uploaded_files)
        st.success(f"**{n}** file{'s' if n != 1 else ''} uploaded successfully!")
        
        # Advanced options
        with st.expander("Advanced Options", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                show_raw = st.checkbox("Show raw extracted text", value=False)
            with col2:
                show_clean = st.checkbox("Show cleaned text", value=False)
        
        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_btn = st.button("Analyze All Resumes with AI", type="primary", use_container_width=True)
        
        if analyze_btn:
            render_section_header("Analysis Results")
            errors = []
            for i, save_path in enumerate(save_paths):
                with st.spinner(f"Analyzing **{save_path.name}** ({i + 1}/{len(save_paths)})..."):
                    result = process_single_resume(save_path)
                
                if "error" in result:
                    errors.append((save_path.name, result["error"]))
                    st.error(f"**{save_path.name}**: {result['error']}")
                else:
                    # Save to sectioned folder so results persist (Browse Candidates / AI Search)
                    sectioned_output = {
                        "source_txt": save_path.name,
                        "sections": result["sections"]
                    }
                    sectioned_path = dirs["sectioned"] / f"{save_path.stem}.json"
                    sectioned_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(sectioned_path, "w", encoding="utf-8") as f:
                        json.dump(sectioned_output, f, indent=2, ensure_ascii=False)

                    with st.expander(f"{save_path.name}", expanded=(i == 0)):
                        display_sections(result["sections"])
                        
                        if show_raw:
                            with st.expander("Raw Extracted Text", expanded=False):
                                st.text_area("Raw Text", result["raw_text"], height=200, label_visibility="collapsed", key=f"raw_{save_path.stem}_{i}")
                        
                        if show_clean:
                            with st.expander("Cleaned Text", expanded=False):
                                st.text_area("Cleaned Text", result["clean_text"], height=200, label_visibility="collapsed", key=f"clean_{save_path.stem}_{i}")
                        
                        json_output = json.dumps(result["sections"], indent=2, ensure_ascii=False)
                        st.download_button(
                            label="Download JSON",
                            data=json_output,
                            file_name=f"{save_path.stem}_structured.json",
                            mime="application/json",
                            use_container_width=True,
                            key=f"download_{save_path.stem}_{i}"
                        )
            
            if errors:
                st.warning(f"{len(errors)} of {len(save_paths)} file(s) could not be processed.")
            else:
                st.success("Analysis results saved. They will appear in **Browse Candidates** and **AI Search** (run **Build Embeddings** in Pipeline Manager if you use AI Search).")


def render_tab_pipeline(stats: dict, process_all_pdfs, section_all_resumes, build_vector_store, export_chroma_csv):
    """Tab 2: Pipeline Manager"""
    render_section_header("Data Processing Pipeline")
    
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
        render_pipeline_card("Step 1: Extract Text", "Convert PDF files to plain text using pdfplumber")
        if st.button("Run Extraction", key="extract", use_container_width=True):
            with st.spinner("Extracting text from PDFs..."):
                try:
                    process_all_pdfs()
                    st.success("PDF extraction complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        render_pipeline_card("Step 2: AI Structuring", "Use LLM to extract structured resume data")
        if st.button("Run AI Processing", key="section", use_container_width=True):
            with st.spinner("Processing with AI (this may take a while)..."):
                try:
                    section_all_resumes()
                    st.success("AI processing complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Full pipeline
    render_pipeline_card("Run Complete Pipeline", "Execute all 3 steps: Extract → Structure → Embed", highlight=True)
    
    if st.button("Run Full Pipeline", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("Step 1/3: Extracting text from PDFs...")
            process_all_pdfs()
            progress_bar.progress(33)
            
            status_text.info("Step 2/3: Processing with AI...")
            section_all_resumes()
            progress_bar.progress(66)
            
            status_text.info("Step 3/3: Building embeddings...")
            build_vector_store()
            progress_bar.progress(100)
            
            status_text.success("Pipeline complete! AI Search is ready.")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline error: {e}")

    # Step 3: Build Embeddings
    st.markdown("<br>", unsafe_allow_html=True)
    render_pipeline_card("Step 3: Build Embeddings", "Create vector embeddings for AI-powered search")
    
    if st.button("Build Embeddings", key="build_embeddings", use_container_width=True):
        with st.spinner("Building embeddings (this may take a minute)..."):
            try:
                build_vector_store()
                st.success("Embeddings built! AI Search is now ready.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Export utility
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Export Database to CSV"):
        include_emb = st.checkbox("Include embeddings in CSV (large file)", value=False)
        if st.button("Export to CSV", key="export_db", use_container_width=True):
            with st.spinner("Exporting Chroma DB to CSV..."):
                try:
                    n = export_chroma_csv(include_embeddings=include_emb)
                    st.success(f"Exported {n} rows to data/chroma_export.csv")
                    with open("data/chroma_export.csv", "rb") as fh:
                        st.download_button("Download CSV", fh, file_name="chroma_export.csv")
                except Exception as e:
                    st.error(f"Error exporting DB: {e}")


def render_tab_browse(dirs: dict, search_resumes=None, query_available: bool = False):
    """Tab 3: Browse Candidates"""
    render_section_header("Candidate Database")
    
    structured_files = list(dirs["sectioned"].glob("*.json"))
    
    if not structured_files:
        render_empty_state("No Candidates Yet", "Run the processing pipeline to add resumes to the database.")
        return
    
    # Stats and search
    col1, col2 = st.columns([1, 2])
    with col1:
        render_stat_card(len(structured_files), "Total Candidates", "#667eea")
    with col2:
        search_term = st.text_input("Search candidates...", "", placeholder="Enter name or ID", key="candidate_search")
    
    # Track search changes to reset pagination
    if "last_search" not in st.session_state:
        st.session_state.last_search = ""
    if "browse_page" not in st.session_state:
        st.session_state.browse_page = 1
    
    # Reset to page 1 when search changes
    if search_term != st.session_state.last_search:
        st.session_state.browse_page = 1
        st.session_state.last_search = search_term
    
    # Filter files
    search_term = search_term.strip()
    if search_term:
        filtered_files = [f for f in structured_files if search_term.lower() in f.stem.lower()]
        if filtered_files:
            st.success(f"Found {len(filtered_files)} candidate(s) matching '{search_term}'")
        else:
            st.warning(f"No candidates found matching '{search_term}'")
    else:
        filtered_files = structured_files

    # Skill-based search
    st.markdown("<br>", unsafe_allow_html=True)
    ai_query = st.text_input("Search by skills (e.g., 'Python', 'Java developer')", "", key="browse_skill_search")
    ai_k = st.slider("Top k results", min_value=1, max_value=10, value=5, key="browse_k_slider")

    if ai_query and st.button("Search Skills", key="ai_search"):
        if query_available and search_resumes:
            try:
                with st.spinner("Searching candidates..."):
                    results = search_resumes(ai_query, n_results=ai_k)
                
                if not results:
                    st.info("No candidates found with those skills.")
                else:
                    for r in results:
                        match_badge = "Exact Match" if r.get("match_type") == "keyword" else "Semantic Match"
                        st.markdown(f"**Candidate {r['id']}** — {match_badge}")
                        if r.get("matched_keywords"):
                            st.markdown(f"*Matched: {', '.join(r['matched_keywords'])}*")
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
    
    if st.session_state.browse_page > total_pages:
        st.session_state.browse_page = 1
    
    with col2:
        page = st.selectbox("Page", range(1, total_pages + 1), index=st.session_state.browse_page - 1, key="browse_page_select", label_visibility="collapsed")
        st.session_state.browse_page = page
    with col3:
        st.caption(f"Page {page} of {total_pages}")
    
    start_idx = (page - 1) * items_per_page
    page_files = filtered_files[start_idx:start_idx + items_per_page]
    
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
                    st.markdown(f'<p style="color: #667eea;">{" • ".join(sections.get("skills", []))}</p>', unsafe_allow_html=True)
                st.divider()
                display_sections(sections)
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")


def render_tab_ai_search(answer_question, query_available: bool = False, error_msg: str = None, dirs: dict = None):
    """Tab 4: AI Search"""
    render_section_header("Ask AI About Candidates")
    
    if not query_available:
        st.warning("Query system not available. Make sure ChromaDB embeddings are set up.")
        if error_msg:
            st.error(f"**Error:** {error_msg}")
        st.info("**Fix:** Go to Pipeline Manager → Click 'Build Embeddings' (Step 3)")
        return
    
    # Instructions
    render_instructions_card(
        "What can you ask?",
        [
            '"Does any candidate know Python?"',
            '"Show me candidates with machine learning experience"',
            '"Who has worked at a startup?"',
            '"Find candidates with SQL and data analysis skills"',
            '"Which candidates have a Master\'s degree?"'
        ]
    )
    
    # Question input
    st.markdown("<br>", unsafe_allow_html=True)
    question = st.text_input("Ask a question about candidates:", placeholder="e.g., Does this resume mention Python?", key="ai_question")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        num_results = st.slider("Number of resumes to search", 3, 10, 5, key="ai_num_results")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_btn = st.button("Ask AI", type="primary", use_container_width=True)
    
    # Clear PDF viewer when user does something else (avoids reopening on scroll or Match Candidates)
    if search_btn:
        if "ai_search_view_pdf" in st.session_state:
            del st.session_state["ai_search_view_pdf"]
    if "ai_last_num_results" in st.session_state and st.session_state.ai_last_num_results != num_results:
        if "ai_search_view_pdf" in st.session_state:
            del st.session_state["ai_search_view_pdf"]
    st.session_state["ai_last_num_results"] = num_results
    
    if search_btn and question:
        with st.spinner("AI is searching and analyzing resumes..."):
            try:
                result = answer_question(question, n_results=num_results)
                st.session_state["ai_search_last_result"] = result
            except Exception as e:
                if "Collection" in str(e):
                    st.error("ChromaDB not set up yet! Run the pipeline first.")
                else:
                    st.error(f"Error: {e}")
    elif search_btn:
        st.warning("Please enter a question first.")

    # Show last result (answer + sources with View PDF)
    result = st.session_state.get("ai_search_last_result")
    if result:
        render_section_header("AI Answer")
        st.markdown(f'<div class="card">{result["answer"]}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Sources** ({result['num_results']} resumes analyzed)")
        for src in result["sources"]:
            cid = src["id"]
            matched_kw = src.get("matched_keywords", [])
            col_text, col_btn = st.columns([1, 0.2])
            with col_text:
                if matched_kw:
                    st.markdown(f"- **Candidate {cid}** - Matched: **{', '.join(matched_kw)}**")
                else:
                    st.markdown(f"- **Candidate {cid}** - Relevance: {int(src['score'] * 100)}%")
            with col_btn:
                if dirs:
                    pdf_path = get_candidate_pdf_path(dirs, cid)
                    if pdf_path:
                        if st.button("View PDF", key=f"view_ai_{cid}"):
                            st.session_state["ai_search_view_pdf"] = cid
                            st.rerun()

    # Pop-up PDF viewer (AI Search)
    if st.session_state.get("ai_search_view_pdf") and dirs:
        cid = st.session_state["ai_search_view_pdf"]
        if _dialog_decorator:
            _pdf_modal(cid, dirs, "ai_search_view_pdf")
        else:
            with st.expander(f"Viewing PDF: Candidate {cid}", expanded=True):
                _render_pdf_content(cid, dirs, "ai_search_view_pdf", "close_ai_pdf")


def render_tab_matching(match_top_candidates, matching_available: bool = False, error_msg: str = None, dirs: dict = None):
    """Tab 5: Job Matching"""
    render_section_header("Match Candidates to Job Description")
    
    if not matching_available:
        st.warning("Matching system not available. Check that match_resumes.py exists.")
        if error_msg:
            st.error(f"**Error:** {error_msg}")
        return
    
    # Instructions
    render_instructions_card(
        "How it works",
        [
            "Paste or type a job description below",
            "Select how many candidates to evaluate",
            'Click "Match Candidates" to get scored results'
        ],
        ordered=True,
        footer="**Each candidate gets:** Score (0-100), Strengths, Gaps, and Reasoning"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Job description input
    job_description = st.text_area(
        "Job Description",
        placeholder="Paste the job description here...",
        height=250,
        key="job_description"
    )
    
    # Options
    col1, col2 = st.columns(2)
    with col1:
        n_candidates = st.slider("Number of candidates to evaluate", 5, 30, 10, key="n_match_candidates")
    with col2:
        st.info(f"Estimated time: ~{n_candidates * 2} seconds")
    
    # Match button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        match_btn = st.button("Match Candidates", type="primary", use_container_width=True)
    
    # Clear PDF viewer when user does something else (avoids reopening on scroll or new match)
    if match_btn:
        for key in ("ai_search_view_pdf", "match_view_pdf"):
            if key in st.session_state:
                del st.session_state[key]
    if "match_last_n_candidates" in st.session_state and st.session_state.match_last_n_candidates != n_candidates:
        if "match_view_pdf" in st.session_state:
            del st.session_state["match_view_pdf"]
    st.session_state["match_last_n_candidates"] = n_candidates
    
    if match_btn and job_description.strip():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total):
            progress_bar.progress(current / total)
            status_text.info(f"Analyzing candidate {current}/{total}...")
        
        with st.spinner("AI is analyzing candidates..."):
            try:
                results = match_top_candidates(job_description.strip(), n_candidates=n_candidates, progress_callback=update_progress)
                st.session_state["match_last_results"] = results
                progress_bar.progress(1.0)
                status_text.success(f"Analyzed {len(results)} candidates!")
            except Exception as e:
                st.error(f"Error during matching: {e}")

    # Show last match results (candidate list with View PDF)
    results = st.session_state.get("match_last_results", [])
    if results:
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_header(f"Top {len(results)} Candidates")
        for i, r in enumerate(results, 1):
            render_candidate_result(r, rank=i, expanded=(i <= 3), dirs=dirs)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            "Download Results (JSON)",
            json.dumps(results, indent=2, ensure_ascii=False),
            file_name="matching_results.json",
            mime="application/json",
            use_container_width=True
        )
    if match_btn and not job_description.strip():
        st.warning("Please enter a job description first.")

    # Pop-up PDF viewer (Job Matching)
    if st.session_state.get("match_view_pdf") and dirs:
        cid = st.session_state["match_view_pdf"]
        if _dialog_decorator:
            _pdf_modal(cid, dirs, "match_view_pdf")
        else:
            with st.expander(f"Viewing PDF: Candidate {cid}", expanded=True):
                _render_pdf_content(cid, dirs, "match_view_pdf", "close_match_pdf")
