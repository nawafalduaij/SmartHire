import os
import zipfile
from pathlib import Path

# Root project directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Define folders
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "fake_resumes"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS = PROJECT_ROOT / "outputs"
LOGS = PROJECT_ROOT / "logs"

# Create folders
for path in [DATA_RAW, DATA_PROCESSED, OUTPUTS, LOGS]:
    path.mkdir(parents=True, exist_ok=True)

print("Project folders created")

# Path to dataset zip (must be placed manually)
ZIP_PATH = PROJECT_ROOT / "data" / "fake_resumes.zip"

if not ZIP_PATH.exists():
    raise FileNotFoundError(
        f"Dataset zip not found at {ZIP_PATH}\n"
        )

# Extract dataset
with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
    zip_ref.extractall(DATA_RAW)

print(f"Dataset extracted to: {DATA_RAW}")

# Show sample files
all_files = list(DATA_RAW.rglob("*.*"))
print(f"Total files found: {len(all_files)}")
print("Sample files:")
for f in all_files[:10]:
    print("-", f.relative_to(DATA_RAW))
    