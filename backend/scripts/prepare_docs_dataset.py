import json
from pathlib import Path
from datasets import load_dataset

LANG = "python"
TRAIN_LIMIT = 50000
VALID_LIMIT = 2000

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_OUT = OUT_DIR / f"{LANG}_train_docs.jsonl"
VALID_OUT = OUT_DIR / f"{LANG}_valid_docs.jsonl"


def clean(text: str) -> str:
    return " ".join(text.strip().split())


def main():
    print("Loading dataset...")
    ds = load_dataset("code_search_net", LANG, trust_remote_code=True)

    def write_split(split, out_path: Path, limit: int) -> int:
        written = 0
        skipped = 0

        with open(out_path, "w", encoding="utf-8") as f:
            for row in split:
                code = row.get("func_code_string", "") or row.get("whole_func_string", "")
                doc = row.get("func_documentation_string", "")

                if not isinstance(code, str) or not isinstance(doc, str):
                    skipped += 1
                    continue

                code = code.strip()
                doc = clean(doc)

                # basic filtering
                if len(code) < 20 or len(doc) < 10:
                    skipped += 1
                    continue

                f.write(json.dumps({"code": code, "doc": doc}, ensure_ascii=False) + "\n")
                written += 1

                if written % 5000 == 0:
                    print(f"{out_path.name}: written {written}")

                if written >= limit:
                    break

        print(f"Saved {out_path} | written={written} | skipped={skipped}")
        return written

    print("Writing train...")
    train_n = write_split(ds["train"], TRAIN_OUT, TRAIN_LIMIT)

    print("Writing validation...")
    valid_n = write_split(ds["validation"], VALID_OUT, VALID_LIMIT)

    print("DONE ✅")
    print("Train rows:", train_n)
    print("Valid rows:", valid_n)


if __name__ == "__main__":
    main()