from pathlib import Path
import json
import re
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "resumes_clean"

SECTION_PATTERN = re.compile(r"^[A-Z][A-Z \-/]{2,}$")

def inspect_sections(sample_size=100):
    section_counter = Counter()
    files = list(INPUT_DIR.glob("*.json"))[:sample_size]

    for file in files:
        data = json.loads(file.read_text(encoding="utf-8", errors="ignore"))
        text = data.get("clean_text", "")

        for line in text.splitlines():
            line = line.strip()
            if SECTION_PATTERN.match(line):
                section_counter[line] += 1

    print("Most common detected section headers:\n")
    for section, count in section_counter.most_common(30):
        print(f"{section}  ->  {count}")

if __name__ == "__main__":
    inspect_sections()
