"""
SmartHire - Helper Functions
Data processing and utility functions
"""
import sys
from pathlib import Path

# Add scripts folder to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pdf_extractor import extract_text_from_pdf as extract_pdf_pdfplumber
from section_resumes import clean_text, section_with_llm

# Directory paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "fake_resumes"
PROCESSED_TEXT_DIR = DATA_DIR / "processed" / "resumes_text"
PROCESSED_SECTIONED_DIR = DATA_DIR / "processed" / "resumes_sectioned_json"
UPLOADS_DIR = DATA_DIR / "uploads"


def get_dataset_stats() -> dict:
    """Get statistics about the current dataset"""
    raw_pdfs = list(RAW_DIR.glob("*.pdf"))
    text_files = list(PROCESSED_TEXT_DIR.glob("*.txt"))
    sectioned_files = list(PROCESSED_SECTIONED_DIR.glob("*.json"))
    
    return {
        "raw_pdfs": len(raw_pdfs),
        "extracted_text": len(text_files),
        "sectioned_json": len(sectioned_files)
    }


def process_single_resume(pdf_path: Path) -> dict:
    """
    Full pipeline for a single resume:
    1. Extract text from PDF
    2. Clean and structure with LLM
    """
    # Step 1: Extract text from PDF
    raw_text = extract_pdf_pdfplumber(pdf_path)
    
    if not raw_text.strip():
        return {"error": "Could not extract text from PDF"}
    
    # Step 2: Clean the text
    cleaned_text = clean_text(raw_text)
    
    # Step 3: Use LLM to structure sections
    try:
        sections = section_with_llm(cleaned_text)
    except Exception as e:
        return {"error": f"LLM processing failed: {e}"}
    
    return {
        "filename": pdf_path.name,
        "raw_text": raw_text,
        "clean_text": cleaned_text,
        "sections": sections
    }


def get_directories() -> dict:
    """Get all directory paths"""
    return {
        "project_root": PROJECT_ROOT,
        "data": DATA_DIR,
        "raw": RAW_DIR,
        "text": PROCESSED_TEXT_DIR,
        "sectioned": PROCESSED_SECTIONED_DIR,
        "uploads": UPLOADS_DIR
    }
