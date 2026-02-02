"""
SmartHire - Custom CSS Styles
"""
import streamlit as st


def load_css():
    """Load custom CSS styling for the app (dark mode only)."""
    st.markdown("""
    <style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .hero-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .hero-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #262730 0%, #3d3d4a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #3d3d4a;
    }
    
    .stat-card-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stat-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .stat-card p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    /* Section headers */
    .section-header {
        background: #262730;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #667eea;
        color: #fafafa;
    }
    
    .section-header h3 { color: #fafafa; }
    
    /* Card container */
    .card {
        background: #262730;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        border: 1px solid #3d3d4a;
        color: #e0e0e0;
    }
    
    .card h4, .card li { color: #e0e0e0; }
    
    /* Experience card */
    .exp-card {
        background: #262730;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border-left: 3px solid #667eea;
        color: #e0e0e0;
    }
    
    /* Skills tags */
    .skill-tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #1e1e28;
        margin: 1rem 0;
        color: #e0e0e0;
    }
    
    .upload-area h4, .upload-area p { color: #e0e0e0; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* PDF viewer dialog: make it large (width set via st.dialog width="large", height via CSS) */
    [data-testid="stDialog"] {
        max-height: 90vh !important;
        min-height: 80vh !important;
    }
    [data-testid="stDialog"] [data-testid="stVerticalBlock"] {
        min-height: 75vh !important;
    }
    
    /* Dark mode: app and main area */
    .stApp { background-color: #0e1117 !important; }
    .main { background-color: #0e1117 !important; }
    .main .block-container { background-color: transparent !important; color: #fafafa !important; }
    .main .block-container p, .main .block-container li { color: #e0e0e0 !important; }
    .main h1, .main h2, .main h3, .main h4 { color: #fafafa !important; }
    .main [data-testid="stVerticalBlock"] { background: transparent !important; }
    .stat-card { background: linear-gradient(135deg, #262730 0%, #3d3d4a 100%) !important; border-color: #3d3d4a !important; color: #e0e0e0 !important; }
    .stat-card h3, .stat-card p { color: #e0e0e0 !important; }
    [data-testid="stFileUploader"] { background: #1e1e28 !important; border-radius: 12px; }
    [data-testid="stFileUploader"] section { background: #1e1e28 !important; border: 2px dashed #667eea !important; }
    [data-testid="stSidebar"] { background-color: #0e1117 !important; }
    [data-testid="stSidebar"] .stMarkdown { color: #fafafa !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #e0e0e0 !important; }
    </style>
    """, unsafe_allow_html=True)
