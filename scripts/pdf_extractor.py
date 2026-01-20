from pathlib import Path
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "fake_resumes"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_text"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(pdf_path: Path) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Failed to process {pdf_path.name}: {e}")
    return text


def process_all_pdfs():
    pdf_files = list(RAW_DIR.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        output_file = PROCESSED_DIR / f"{pdf_file.stem}.txt"

        if output_file.exists():
            continue

        text = extract_text_from_pdf(pdf_file)

        if text.strip():
            output_file.write_text(text, encoding="utf-8")
        else:
            print(f"No text extracted from {pdf_file.name}")

    print("PDF extraction completed")


if __name__ == "__main__":
    process_all_pdfs()