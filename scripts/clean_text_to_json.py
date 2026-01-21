"""
Week 6 – Clean resume TXT files and convert to clean JSON
Source of truth: TXT files
"""

from pathlib import Path
import json
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_text"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_clean"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove extra spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def process_all_txt_files():
    txt_files = list(INPUT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} TXT files")

    for txt_file in txt_files:
        raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(raw_text)

        output = {
            "source_txt": txt_file.name,
            "clean_text": cleaned
        }

        output_path = OUTPUT_DIR / f"{txt_file.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ Clean JSON files created successfully")


if __name__ == "__main__":
    process_all_txt_files()