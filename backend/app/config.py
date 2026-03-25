# app/config.py
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

# ── FIX 1: BaseSettings (not BaseModel) for env var + .env file support ──────
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]
    _PYDANTIC_V2 = False

from pydantic import model_validator


_DEFAULT_FAISS_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss"


class Settings(BaseSettings):
    """
    Application configuration.
    """

    # ── AI model identifiers ──────────────────────────────────────────────────
    codebert_model: str = "microsoft/codebert-base"
    # Use base model - we'll use proper prompting for code-to-text
    codet5_model: str = "Salesforce/codet5-base"
    hf_token: str = ""

    # ── Auth & OAuth ──────────────────────────────────────────────────────────
    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: str = ""

    # ── Mail ──────────────────────────────────────────────────────────────────
    mail_username: str = ""
    mail_password: str = ""

    # ── FAISS paths ───────────────────────────────────────────────────────────
    faiss_dir: Path = _DEFAULT_FAISS_DIR
    index_path: Optional[Path] = None
    meta_path: Optional[Path] = None

    # ── Device ────────────────────────────────────────────────────────────────
    device: Literal["cuda", "cpu", "mps"] = "cpu"

    @model_validator(mode="after")
    def _derive_faiss_paths(self) -> "Settings":
        """Set index_path / meta_path relative to faiss_dir unless explicitly overridden."""
        if self.index_path is None:
            self.index_path = self.faiss_dir / "codebert.index"
        if self.meta_path is None:
            self.meta_path = self.faiss_dir / "meta.jsonl"
        return self

    def validate_paths(self, raise_on_missing: bool = False) -> list[str]:
        """Check that FAISS index and metadata files exist."""
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

    if _PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
        )


if not _PYDANTIC_V2:
    
    class _SettingsV1Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    Settings.Config = _SettingsV1Config


settings = Settings()