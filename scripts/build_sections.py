"""
Build resume sections using hybrid approach:
1) Line-based detection
2) Regex fallback (from advanced processor)
"""

from pathlib import Path
import json
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_clean"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_structured"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SECTION_KEYWORDS = {
    "summary": ["summary", "professional summary", "profile", "overview"],
    "experience": ["experience", "professional experience", "work experience", "employment"],
    "education": ["education", "education and training", "academic"],
    "skills": ["skills", "skill highlights", "core qualifications", "competencies"],
    "certifications": ["certifications", "licenses"]
}

REGEX_PATTERNS = {
    "summary": r"(?i)(summary|objective|profile|overview)[\s:]+(.*?)(?=\n[A-Z][a-z ]+|\Z)",
    "experience": r"(?i)(experience|work history|employment)[\s:]+(.*?)(?=\n[A-Z][a-z ]+|\Z)",
    "education": r"(?i)(education|academic|education and training)[\s:]+(.*?)(?=\n[A-Z][a-z ]+|\Z)",
    "skills": r"(?i)(skills|competencies|technologies|core qualifications)[\s:]+(.*?)(?=\n[A-Z][a-z ]+|\Z)",
    "certifications": r"(?i)(certifications?|licenses?)[\s:]+(.*?)(?=\n[A-Z][a-z ]+|\Z)",
}


def normalize(text: str) -> str:
    return text.lower().strip()


def detect_section(line: str):
    line_norm = normalize(line)
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if line_norm == kw:
                return section
    return None


def build_sections(text: str):
    sections = {k: "" for k in SECTION_KEYWORDS}
    sections["other"] = ""

    # 1) Line-based pass
    current = "other"
    buffer = {k: [] for k in sections}

    for line in text.splitlines():
        if not line.strip():
            continue

        detected = detect_section(line)
        if detected:
            current = detected
            continue

        buffer[current].append(line)

    for k in buffer:
        sections[k] = "\n".join(buffer[k]).strip()

    # 2) Regex fallback
    for section, pattern in REGEX_PATTERNS.items():
        if not sections.get(section):
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                sections[section] = match.group(2).strip()

    return {k: v for k, v in sections.items() if v}


def process_files():
    files = list(INPUT_DIR.glob("*.json"))
    print(f"Found {len(files)} clean resumes")

    for file in files:
        data = json.loads(file.read_text(encoding="utf-8", errors="ignore"))
        clean_text = data.get("clean_text", "")

        structured = build_sections(clean_text)

        output = {
            "source_txt": data.get("source_txt"),
            "sections": structured
        }

        out_path = OUTPUT_DIR / file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ Sections built using hybrid logic")


if __name__ == "__main__":
    process_files()