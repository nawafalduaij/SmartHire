"""
SmartHire - Shared Configuration
Centralized paths, LLM clients, and settings
"""
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI

# ===========================================
# PATHS
# ===========================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Data paths
RAW_DIR = DATA_DIR / "raw" / "fake_resumes"
TEXT_DIR = DATA_DIR / "processed" / "resumes_text"
JSON_DIR = DATA_DIR / "processed" / "resumes_sectioned_json"
CHROMA_DIR = DATA_DIR / "chroma_db"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure directories exist
for d in [RAW_DIR, TEXT_DIR, JSON_DIR, CHROMA_DIR, UPLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ===========================================
# ENVIRONMENT
# ===========================================
load_dotenv(PROJECT_ROOT / ".env")

# ===========================================
# LLM CLIENTS
# ===========================================

# OpenRouter (for query and matching)
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Groq (for resume sectioning - faster, free tier)
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Ollama (local fallback)
ollama_client = OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

# ===========================================
# MODEL SETTINGS
# ===========================================
OPENROUTER_MODEL = "deepseek/deepseek-chat"
GROQ_PRIMARY = "llama-3.3-70b-versatile"
GROQ_FALLBACK = "llama-3.1-8b-instant"
OLLAMA_MODEL = "llama3.2"
