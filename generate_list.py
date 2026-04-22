import json
import re
from pathlib import Path

PDF_DIR = Path("pdfs")
LIST_FILE = PDF_DIR / "list.json"

pattern = re.compile(r"^(\d{6})_(.+)\.pdf$", re.IGNORECASE)

data = {}

if PDF_DIR.exists():
    for pdf_file in sorted(PDF_DIR.glob("*.pdf")):
        match = pattern.match(pdf_file.name)
        if not match:
            continue

        date_key = match.group(1)
        label = match.group(2)

        if date_key not in data:
            data[date_key] = {}

        data[date_key][label] = pdf_file.name

sorted_data = {
    date: dict(sorted(labels.items()))
    for date, labels in sorted(data.items())
}

PDF_DIR.mkdir(parents=True, exist_ok=True)

with open(LIST_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted_data, f, ensure_ascii=False, indent=2)

print(f"Generated {LIST_FILE} with {sum(len(v) for v in sorted_data.values())} entries.")
