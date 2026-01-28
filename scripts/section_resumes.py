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

# Groq - Free & Fast LLM inference
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Using 70B model for better JSON handling on complex resumes
MODEL = "llama-3.3-70b-versatile"

# Rate limit settings (Groq free tier - 70B has lower limits)
DELAY_BETWEEN_CALLS = 5  # seconds between API calls to avoid rate limits

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

def section_with_llm(text: str, retries: int = 3) -> dict:
    """Call LLM to extract sections from resume text with retry logic."""
    last_error = None
    
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
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
            last_error = e
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"\n  Retry {attempt + 1}/{retries} after error: {str(e)[:50]}...")
                time.sleep(wait_time)
            continue
    
    # All retries failed
    raise last_error

def process_all_txt():
    files = list(INPUT_DIR.glob("*.txt"))
    done_files = {
        f.stem for f in OUTPUT_DIR.glob("*.json")
    }
    
    pending_files = [f for f in files if f.stem not in done_files]

    print(f"Found {len(files)} resume files")
    print(f"Already processed: {len(done_files)}")
    print(f"Remaining: {len(pending_files)}")
    
    if not pending_files:
        print("All files already processed!")
        return

    for i, file in enumerate(pending_files):
        print(f"[{i+1}/{len(pending_files)}] Processing {file.name}...", end=" ")
        
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
            
            # Delay between calls to avoid rate limits
            if i < len(pending_files) - 1:  # Don't delay after last file
                time.sleep(DELAY_BETWEEN_CALLS)

        except Exception as e:
            print(f"✗ Error: {e}")

    print("Done. All resumes processed.")

if __name__ == "__main__":
    process_all_txt()
