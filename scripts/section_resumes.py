from pathlib import Path
import json
import re
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_text"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_sectioned_json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ===========================================
# CLIENT CONFIGURATION
# ===========================================

# Groq - Free & Fast LLM inference (cloud)
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Ollama - Local LLM (unlimited, no rate limits)
# Make sure Ollama is running: ollama serve
ollama_client = OpenAI(
    api_key="ollama",  # Ollama doesn't need a real key
    base_url="http://localhost:11434/v1"
)

# ===========================================
# MODEL CONFIGURATION
# ===========================================
# Priority order:
# 1. Groq 70B (best quality, 100k tokens/day)
# 2. Groq 8B (good quality, 500k tokens/day)
# 3. Ollama local (unlimited, requires local setup)

GROQ_PRIMARY = "llama-3.3-70b-versatile"
GROQ_FALLBACK = "llama-3.1-8b-instant"
OLLAMA_MODEL = "llama3.2"  # or "llama3.1:8b", "mistral", etc.

# Track current provider and model
current_provider = "groq"  # "groq" or "ollama"
current_model = GROQ_PRIMARY

# Rate limit settings
DELAY_BETWEEN_CALLS = 3  # seconds between API calls (only for cloud)

SYSTEM_PROMPT = """You are a strict JSON generator. Extract resume information into EXACTLY this schema:

{
  "summary": "2-3 sentence professional summary",
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Start - End",
      "location": "City, State",
      "responsibilities": ["responsibility 1", "responsibility 2"]
    }
  ],
  "education": [
    {
      "degree": "Degree Type",
      "field": "Field of Study",
      "institution": "School Name",
      "dates": "Year or Date Range",
      "gpa": "GPA if mentioned"
    }
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "certifications": ["certification1", "certification2"],
  "other": ["other relevant info"]
}

STRICT RULES:
1. Return ONLY the JSON object - no markdown, no explanations, no extra text
2. EVERY experience item MUST be an object with: title, company, dates, location, responsibilities
3. EVERY education item MUST be an object with: degree, field, institution, dates, gpa
4. Skills must be a flat array of strings - no duplicates, normalize to title case
5. Certifications must be a flat array of strings
6. Use empty string "" for missing fields, empty array [] for missing sections
7. Extract ALL experience and education entries from the resume
8. Do NOT invent information - only extract what is explicitly stated"""

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)

    return text.strip()

def get_current_client():
    """Get the appropriate client based on current provider."""
    if current_provider == "ollama":
        return ollama_client
    return groq_client


def switch_to_ollama():
    """Switch to Ollama local model."""
    global current_provider, current_model
    current_provider = "ollama"
    current_model = OLLAMA_MODEL
    print(f"\n  🖥️ Switching to Ollama local model ({OLLAMA_MODEL})...")


def section_with_llm(text: str, retries: int = 3) -> dict:
    """Call LLM to extract sections from resume text with retry logic and model fallback."""
    global current_provider, current_model
    last_error = None
    
    for attempt in range(retries):
        try:
            client = get_current_client()
            
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            
            # Handle empty response
            if not content or not content.strip():
                raise ValueError("Empty response from LLM")
            
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```json?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
            
            return json.loads(content)
            
        except Exception as e:
            error_str = str(e)
            last_error = e
            
            # Only handle rate limits for Groq (cloud)
            if current_provider == "groq":
                # Check if it's a daily token limit error
                if "429" in error_str and "tokens per day" in error_str.lower():
                    if current_model == GROQ_PRIMARY:
                        print(f"\n  ⚠️ Daily limit hit on 70B, switching to 8B...")
                        current_model = GROQ_FALLBACK
                        time.sleep(2)
                        continue
                    elif current_model == GROQ_FALLBACK:
                        # Both Groq models exhausted, try Ollama
                        switch_to_ollama()
                        continue
                
                # Any 429 error on 8B model -> try Ollama
                if "429" in error_str and current_model == GROQ_FALLBACK:
                    switch_to_ollama()
                    continue
            
            # Ollama connection error - helpful message
            if current_provider == "ollama" and "Connection" in error_str:
                print(f"\n  ❌ Ollama not running! Start it with: ollama serve")
                print(f"     Then pull the model: ollama pull {OLLAMA_MODEL}")
            
            # For other errors, do normal retry with backoff
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"\n  Retry {attempt + 1}/{retries} after error: {str(e)[:50]}...")
                time.sleep(wait_time)
            continue
    
    # All retries failed
    raise last_error

def process_all_txt():
    global current_provider, current_model
    
    # Reset to Groq primary at start
    current_provider = "groq"
    current_model = GROQ_PRIMARY
    
    files = list(INPUT_DIR.glob("*.txt"))
    done_files = {
        f.stem for f in OUTPUT_DIR.glob("*.json")
    }
    
    pending_files = [f for f in files if f.stem not in done_files]

    print(f"Found {len(files)} resume files")
    print(f"Already processed: {len(done_files)}")
    print(f"Remaining: {len(pending_files)}")
    print(f"Starting with: {current_provider} / {current_model}")
    print(f"Fallback chain: Groq 70B → Groq 8B → Ollama local")
    
    if not pending_files:
        print("All files already processed!")
        return

    for i, file in enumerate(pending_files):
        # Show current provider if it changed
        provider_tag = "🖥️" if current_provider == "ollama" else "☁️"
        print(f"[{i+1}/{len(pending_files)}] {provider_tag} Processing {file.name}...", end=" ")
        
        try:
            raw = file.read_text(encoding="utf-8", errors="ignore")
            cleaned = clean_text(raw)

            sections = section_with_llm(cleaned)

            output = {
                "source_txt": file.name,
                "sections": sections
            }

            out_path = OUTPUT_DIR / f"{file.stem}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print("✓")
            
            # Only delay for cloud APIs
            if current_provider == "groq" and i < len(pending_files) - 1:
                time.sleep(DELAY_BETWEEN_CALLS)

        except Exception as e:
            print(f"✗ Error: {e}")

    print("Done. All resumes processed.")

if __name__ == "__main__":
    process_all_txt()
