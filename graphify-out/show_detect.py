import json
from pathlib import Path

d = json.loads(Path(".graphify_detect.json").read_text())
print(f"Corpus: {d['total_files']} files · {d['total_words']} words")
print("\nBreakdown:")
for cat in ["code", "document", "paper", "image", "video"]:
    if d.get("files", {}).get(cat):
        print(f"  {cat}: {len(d['files'][cat])} files")
