# app/retriever.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel


@dataclass
class RetrievedExample:
    score: float
    code: str
    doc: str
    language: str


class CodeBERTRetriever:
    def __init__(
        self,
        model_name: str,
        index_path: str,
        meta_path: str,
        device: str = "cuda",
    ):
        self.device = (
            device if torch.cuda.is_available() and device == "cuda" else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model     = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        # ── FIX 3: Wrap file loading with helpful error messages ─────────────
        try:
            self.index = faiss.read_index(index_path)
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load FAISS index from '{index_path}': {e}"
            ) from e

        self.meta: List[dict] = []
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:   # skip blank lines
                        self.meta.append(json.loads(line))
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Metadata file not found: '{meta_path}'. "
                "Run the indexing script before starting the server."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in metadata file '{meta_path}': {e}") from e

        print(
            f"[Retriever] Loaded FAISS index ({self.index.ntotal} vectors) "
            f"and {len(self.meta)} metadata entries."
        )

    # ─────────────────────────────────────────────────────────────────────────
    @torch.no_grad()
    def embed(self, text: str) -> np.ndarray:
        """Embed a code/text string into a normalised float32 vector."""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=True,
        ).to(self.device)

        out    = self.model(**inputs).last_hidden_state
        mask   = inputs["attention_mask"].unsqueeze(-1)
        pooled = (out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)

        # FIX 5: removed redundant .detach() — already inside @torch.no_grad()
        vec = pooled.squeeze(0).cpu().numpy().astype("float32")
        vec /= np.linalg.norm(vec) + 1e-12
        return vec

    # ─────────────────────────────────────────────────────────────────────────
    # FIX 6: Added @torch.no_grad() — consistent and future-safe
    # FIX 4: Moved the "allow top_k=0" comment to inside the method body
    # ─────────────────────────────────────────────────────────────────────────
    @torch.no_grad()
    def search(
        self,
        code: str,
        k: int = 5,
        language: Optional[str] = None,
    ) -> List[RetrievedExample]:
        """
        Retrieve the top-k most similar examples to the given code snippet.

        Args:
            code: Source code to query against the index.
            k: Number of results to return. Passing 0 returns an empty list.
            language: If provided, filter results to this language only.

        Returns:
            List of RetrievedExample ordered by descending similarity score.
        """
        # FIX 1a: correct indentation — was 1 space, now 8
        # Allow callers to pass top_k=0 without crashing
        if k <= 0:
            return []

        query_vec = self.embed(code)[None, :]

        # Over-fetch so language filtering still yields k results
        fetch_k  = min(k * 5, self.index.ntotal) if self.index.ntotal > 0 else k
        scores, idxs = self.index.search(query_vec, max(fetch_k, 1))

        results: List[RetrievedExample] = []

        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            # FIX 1b: correct indentation on continue/break
            # FAISS returns -1 for unfilled slots
            if idx < 0:
                continue

            # FIX 2: bounds check — meta and index can fall out of sync
            if idx >= len(self.meta):
                print(f"[Retriever] Warning: FAISS index returned idx={idx} "
                      f"but meta only has {len(self.meta)} entries. Skipping.")
                continue

            item = self.meta[idx]

            if language and item.get("language", "").lower() != language.lower():
                continue

            results.append(
                RetrievedExample(
                    score=float(score),
                    code=item.get("code", ""),
                    doc=item.get("doc", ""),
                    language=item.get("language", ""),
                )
            )

            if len(results) >= k:
                break

        return results
