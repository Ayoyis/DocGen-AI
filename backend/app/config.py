# app/config.py
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

# ── FIX 1: BaseSettings (not BaseModel) for env var + .env file support ──────
# Pydantic v2 ships BaseSettings in a separate package: pydantic-settings
# Pydantic v1 includes it in pydantic itself
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]
    _PYDANTIC_V2 = False

from pydantic import model_validator


# Anchored to this file — works regardless of the working directory
_DEFAULT_FAISS_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss"


class Settings(BaseSettings):
    """
    Application configuration.

    Every field can be overridden via environment variable or a .env file:
        DEVICE=cpu
        FAISS_DIR=/mnt/models/faiss
        CODEBERT_MODEL=microsoft/codebert-base-mlm
    """

    # ── AI model identifiers ──────────────────────────────────────────────────
    codebert_model: str = "microsoft/codebert-base"
    codet5_model: str = "Salesforce/codet5-base"

    # ── FAISS paths ───────────────────────────────────────────────────────────
    # Override faiss_dir to relocate all FAISS files at once.
    # Override index_path / meta_path individually for custom layouts.
    faiss_dir: Path = _DEFAULT_FAISS_DIR
    index_path: Optional[Path] = None  # auto-derived from faiss_dir (see validator below)
    meta_path: Optional[Path] = None  # auto-derived from faiss_dir (see validator below)

    # ── FIX 4: Literal type rejects invalid device names at startup ───────────
    device: Literal["cuda", "cpu", "mps"] = "cuda"

    # ── FIX 2: Derive sub-paths from faiss_dir so overriding faiss_dir ────────
    # automatically updates index_path and meta_path
    @model_validator(mode="after")
    def _derive_faiss_paths(self) -> "Settings":
        """Set index_path / meta_path relative to faiss_dir unless explicitly overridden."""
        if self.index_path is None:
            self.index_path = self.faiss_dir / "codebert.index"
        if self.meta_path is None:
            self.meta_path = self.faiss_dir / "meta.jsonl"
        return self

    # ── FIX 5: Warn early if FAISS files are missing ─────────────────────────
    def validate_paths(self, raise_on_missing: bool = False) -> list[str]:
        """
        Check that FAISS index and metadata files exist.
        Call this from your lifespan startup to catch missing files early.

        Args:
            raise_on_missing: If True, raises FileNotFoundError instead of returning warnings.

        Returns:
            List of warning strings for any missing paths.
        """
        warnings: list[str] = []

        for label, path in [
            ("FAISS index", self.index_path),
            ("Metadata file", self.meta_path),
        ]:
            if not Path(path).exists():
                msg = (
                    f"{label} not found at '{path}'. "
                    "Run the indexing script before starting the server."
                )
                if raise_on_missing:
                    raise FileNotFoundError(msg)
                warnings.append(msg)

        return warnings

    # ── FIX 3: .env file support ──────────────────────────────────────────────
    if _PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,  # DEVICE and device both work
        )


# For Pydantic v1, we need to define Config separately since we can't use if/else at class body level
if not _PYDANTIC_V2:
    
    class _SettingsV1Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # Monkey-patch the Config class onto Settings
    Settings.Config = _SettingsV1Config


settings = Settings()