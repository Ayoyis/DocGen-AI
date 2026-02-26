from datasets import load_dataset
from pathlib import Path
import json

OUT = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    lang = "python"  # start with python
    ds = load_dataset("code_search_net", lang, trust_remote_code=True)

    out_path = OUT / f"{lang}_train.jsonl"
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        limit = 50000
        for row in ds["train"]:
            code = row.get("func_code_string") or ""
            doc = row.get("func_documentation_string") or ""

            if not code.strip() or not doc.strip():
                continue
            f.write(json.dumps({"language": lang, "code": code, "doc": doc}, ensure_ascii=False) + "\n")
            count += 1
            if count >= limit:
                break

    print("Saved:", out_path)
    print("Rows:", count)

if __name__ == "__main__":
    main()
