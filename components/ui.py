"""
SmartHire - UI Components
Reusable Streamlit UI components
"""
import streamlit as st


def render_hero():
    """Render the hero header section"""
    st.markdown("""
    <div class="hero-header">
        <h1>🎯 SmartHire</h1>
        <p>AI-Powered Intelligent Recruitment Assistant</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(stats: dict):
    """Render the sidebar with stats and system status"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
        st.markdown("### 📊 Dashboard")
        
        # Stats with colored boxes
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom: 10px;">
            <h3>{stats["raw_pdfs"]}</h3>
            <p>📁 Raw PDFs</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom: 10px;">
            <h3>{stats["extracted_text"]}</h3>
            <p>📝 Extracted</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-card stat-card-primary" style="margin-bottom: 10px;">
            <h3>{stats["sectioned_json"]}</h3>
            <p>🤖 AI Processed</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # System status
        st.success("🟢 System Online")
        st.caption("Powered by Groq LLM")


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
                
                # Handle summary (string)
                if section_name == "summary":
                    st.write(content)
                
                # Handle experience (list of objects)
                elif section_name == "experience":
                    for exp in content:
                        if isinstance(exp, dict):
                            title = exp.get("title", "")
                            company = exp.get("company", "")
                            dates = exp.get("dates", "")
                            location = exp.get("location", "")
                            
                            st.markdown(f"**{title}** at {company}")
                            st.caption(f"{dates} | {location}")
                            
                            responsibilities = exp.get("responsibilities", [])
                            if responsibilities:
                                for resp in responsibilities:
                                    st.write(f"• {resp}")
                            st.divider()
                        else:
                            st.write(f"• {exp}")
                
                # Handle education (list of objects)
                elif section_name == "education":
                    for edu in content:
                        if isinstance(edu, dict):
                            degree = edu.get("degree", "")
                            field = edu.get("field", "")
                            institution = edu.get("institution", "")
                            dates = edu.get("dates", "")
                            gpa = edu.get("gpa", "")
                            
                            st.markdown(f"**{degree}** in {field}")
                            st.write(f"{institution}")
                            if dates:
                                st.caption(f"{dates}" + (f" | GPA: {gpa}" if gpa else ""))
                            st.divider()
                        else:
                            st.write(f"• {edu}")
                
                # Handle skills, certifications, other (list of strings)
                elif isinstance(content, list):
                    if section_name == "skills":
                        # Display skills as tags/chips
                        skills_text = " • ".join(content)
                        st.write(skills_text)
                    else:
                        for item in content:
                            st.write(f"• {item}")
                else:
                    st.write(content)


def render_stat_card(value, label: str, color: str = "#667eea"):
    """Render a statistic card"""
    st.markdown(f"""
    <div class="card" style="text-align: center;">
        <h2 style="color: {color}; margin: 0;">{value}</h2>
        <p style="margin: 0.5rem 0 0 0;">{label}</p>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str):
    """Render a section header"""
    st.markdown(f'<div class="section-header"><h3>{title}</h3></div>', unsafe_allow_html=True)


def render_upload_area():
    """Render the upload area with styling"""
    st.markdown("""
    <div class="upload-area">
        <h4>📤 Drop your resumes here</h4>
        <p>Upload one or more PDFs • AI-powered extraction</p>
    </div>
    """, unsafe_allow_html=True)


def render_info_card():
    """Render the info card showing what we extract"""
    st.markdown("""
    <div class="card">
        <h4>✨ What we extract:</h4>
        <ul>
            <li>📋 Professional Summary</li>
            <li>💼 Work Experience</li>
            <li>🎓 Education</li>
            <li>🛠️ Skills & Competencies</li>
            <li>📜 Certifications</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_card(title: str, description: str, highlight: bool = False):
    """Render a pipeline step card"""
    style = 'background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%); border: 2px solid #667eea;' if highlight else ''
    st.markdown(f"""
    <div class="card" style="{style}">
        <h4>{title}</h4>
        <p style="color: #666;">{description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(title: str, message: str):
    """Render an empty state card"""
    st.markdown(f"""
    <div class="card" style="text-align: center; padding: 3rem;">
        <h3>{title}</h3>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_instructions_card(title: str, items: list, ordered: bool = False, footer: str = None):
    """Render an instructions card with a list of items"""
    list_tag = "ol" if ordered else "ul"
    items_html = "".join(f"<li>{item}</li>" for item in items)
    footer_html = f"<p>{footer}</p>" if footer else ""
    
    st.markdown(f"""
    <div class="card">
        <h4>{title}</h4>
        <{list_tag}>{items_html}</{list_tag}>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)


def render_candidate_result(result: dict, rank: int = 1, expanded: bool = False, dirs: dict = None):
    """Render a candidate matching result with score bar and optional View PDF button."""
    from .helpers import get_candidate_pdf_path
    score = result["score"]
    
    # Color based on score
    if score >= 75:
        score_color = "#28a745"
        badge = "🟢 Strong Match"
    elif score >= 60:
        score_color = "#ffc107"
        badge = "🟡 Good Match"
    elif score >= 40:
        score_color = "#fd7e14"
        badge = "🟠 Partial Match"
    else:
        score_color = "#dc3545"
        badge = "🔴 Weak Match"
    
    with st.expander(f"#{rank} Candidate {result['candidate_id']} — **{score}/100** {badge}", expanded=expanded):
        # Score bar
        st.markdown(f"""
        <div style="background: #e0e0e0; border-radius: 10px; height: 20px; margin-bottom: 1rem;">
            <div style="background: {score_color}; width: {score}%; height: 100%; border-radius: 10px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Summary
        st.markdown(f"**📋 Summary:** {result['summary']}")
        
        # Strengths & Gaps
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Strengths:**")
            if result['strengths']:
                for s in result['strengths'][:5]:
                    st.markdown(f"- {s}")
            else:
                st.caption("None identified")
        
        with col2:
            st.markdown("**⚠️ Gaps:**")
            if result['gaps']:
                for g in result['gaps'][:5]:
                    st.markdown(f"- {g}")
            else:
                st.caption("None identified")
        
        # Reasoning
        st.markdown("**💭 Reasoning:**")
        st.write(result['reasoning'])
        
        # Skills
        if result.get('skills'):
            st.markdown("**🛠️ Skills:**")
            st.write(" • ".join(result['skills'][:15]))
        
        # View PDF inline if available
        if dirs:
            pdf_path = get_candidate_pdf_path(dirs, result["candidate_id"])
            if pdf_path:
                if st.button("📄 View PDF", key=f"view_match_{result['candidate_id']}_{rank}"):
                    st.session_state["match_view_pdf"] = result["candidate_id"]
                    st.rerun()
