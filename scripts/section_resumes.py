from pathlib import Path
import json
import re
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_text"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_sectioned_json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "deepseek/deepseek-chat"

SYSTEM_PROMPT = """
You are a strict JSON generator.

Task:
Analyze the resume text and extract structured information.

Sections:
- summary
- experience
- education
- skills
- certifications
- other

Rules:
- Return ONLY valid JSON.
- No explanations.
- No markdown.
- No extra text.
- All keys must exist.
- Use empty values if information is not found.

STRUCTURE RULES:
- summary: a concise professional summary, MAX 3 sentences.
- experience: MUST be a list. Each item represents ONE role, responsibility, or achievement.
- skills: MUST be a list. Extract both explicitly listed skills and clearly implied professional or technical skills.
- education: Extract degrees, fields of study, institutions, or graduation years if mentioned anywhere in the text.
- certifications: MUST be a list if present.
- other: Any remaining relevant information as a list.

FORMATTING RULES:
- Prefer lists over long paragraphs whenever possible.
- Do NOT merge multiple ideas into one list item.
- Keep all text clean and readable.

Output format:

{
  "summary": "",
  "experience": [],
  "education": [],
  "skills": [],
  "certifications": [],
  "other": []
}
"""

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)

    return text.strip()

def section_with_llm(text: str, retries: int = 2) -> dict:
    for attempt in range(retries):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0,
            max_tokens=800
        )

        content = response.choices[0].message.content.strip()

        try:
            return json.loads(content)
        except Exception:
            if attempt == retries - 1:
                raise

def process_all_txt():
    files = list(INPUT_DIR.glob("*.txt"))
    done_files = {
        f.stem for f in OUTPUT_DIR.glob("*.json")
    }

    print(f"Found {len(files)} resume files")
    print(f"Already processed: {len(done_files)}")

    for file in files:
        if file.stem in done_files:
            continue  # skip already processed files

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

        except Exception as e:
            print(f"Failed on {file.name}: {e}")

    print("Done. All resumes processed.")

if __name__ == "__main__":
    process_all_txt()
