# app/retriever.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import faiss
import requests


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
        device: str = "cpu",  # ignored — embeddings now come from HF API
    ):
        self.model_name = model_name
        self.hf_token = os.environ.get("HF_TOKEN", "")
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}

        # ── Load FAISS index ─────────────────────────────────────────────────
        try:
            self.index = faiss.read_index(index_path)
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load FAISS index from '{index_path}': {e}"
            ) from e

        # ── Load metadata ────────────────────────────────────────────────────
        self.meta: List[dict] = []
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
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

    def embed(self, text: str) -> np.ndarray:
        """Embed a code/text string using HF Inference API."""
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": text, "options": {"wait_for_model": True}},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        # Result is a list of token embeddings — mean pool them
        embeddings = np.array(result, dtype="float32")
        if embeddings.ndim == 2:
            vec = embeddings.mean(axis=0)
        else:
            vec = embeddings

        vec /= np.linalg.norm(vec) + 1e-12
        return vec

    def search(
        self,
        code: str,
        k: int = 5,
        language: Optional[str] = None,
    ) -> List[RetrievedExample]:
        """
        Retrieve the top-k most similar examples to the given code snippet.
        """
        if k <= 0:
            return []

        query_vec = self.embed(code)[None, :]

        fetch_k = min(k * 5, self.index.ntotal) if self.index.ntotal > 0 else k
        scores, idxs = self.index.search(query_vec, max(fetch_k, 1))

        results: List[RetrievedExample] = []

        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx < 0:
                continue

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