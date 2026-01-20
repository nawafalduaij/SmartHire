from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "fake_resumes"
TEXT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_text"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_resumes():
    txt_files = list(TEXT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} text files")

    for txt_file in txt_files:
        raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")

        resume_data = {
            "file_name": txt_file.name,
            "raw_text": raw_text,
        }

        output_path = OUTPUT_DIR / f"{txt_file.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2)

    print("Resume JSON files created successfully")

if __name__ == "__main__":
    load_resumes()