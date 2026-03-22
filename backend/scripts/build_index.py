import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

import faiss

LANG = "python"
BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "processed" / f"{LANG}_train_docs.jsonl"

OUT_DIR = BASE / "data" / "faiss"
OUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = OUT_DIR / "codebert.index"
META_PATH = OUT_DIR / "meta.jsonl"

MODEL_NAME = "microsoft/codebert-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Build a smaller index first so you can confirm it works quickly.
LIMIT = 10000  # increase later (e.g., 20000, 100000)

@torch.no_grad()
def embed_code(model, tokenizer, code: str) -> np.ndarray:
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True,
    ).to(DEVICE)

    out = model(**inputs).last_hidden_state
    mask = inputs["attention_mask"].unsqueeze(-1)
    pooled = (out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)

    vec = pooled.squeeze(0).detach().cpu().numpy().astype("float32")
    vec /= (np.linalg.norm(vec) + 1e-12)
    return vec

def main():
    print("IN_PATH:", IN_PATH)
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {IN_PATH}")

    print("Device:", DEVICE)
    print("Loading tokenizer/model:", MODEL_NAME)
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
    model.eval()
    print(f"Loaded model in {time.time() - t0:.1f}s")

    print("Reading JSONL + embedding up to LIMIT =", LIMIT)
    vecs = []
    kept = []
    total_lines = 0
    skipped = 0
    failed = 0

    t1 = time.time()
    with open(IN_PATH, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            try:
                r = json.loads(line)
            except Exception:
                skipped += 1
                continue

            code = r.get("code", "")
            doc = r.get("doc", "")
            if not isinstance(code, str) or not code.strip() or not isinstance(doc, str) or not doc.strip():
                skipped += 1
                continue

            try:
                v = embed_code(model, tokenizer, code)
                vecs.append(v)
                kept.append(r)
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print("Embed error example:", repr(e))
                continue

            if len(vecs) % 100 == 0:
                elapsed = time.time() - t1
                print(f"Embedded {len(vecs)} items... ({elapsed:.1f}s)")
            if len(vecs) >= LIMIT:
                break

    print("Total lines read:", total_lines)
    print("Skipped:", skipped)
    print("Failed embeddings:", failed)
    print("Vectors:", len(vecs))

    if len(vecs) == 0:
        raise RuntimeError("No vectors created. See counts above.")

    X = np.stack(vecs, axis=0)
    print("Vector matrix shape:", X.shape)

    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X)

    faiss.write_index(index, str(INDEX_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Saved index:", INDEX_PATH)
    print("Saved meta:", META_PATH)

if __name__ == "__main__":
    main()
