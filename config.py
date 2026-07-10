import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".cursor",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}

DEFAULT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".sql",
}


@dataclass
class AppConfig:
  codebase_path: Path
  repeat_interval_seconds: int = 40
  run_once: bool = False
  desktop_notify: bool = True
  gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
  llm_model: str = field(
    default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
  )
  llm_fallback_models: tuple[str, ...] = (
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-flash-latest",
  )
  llm_max_retries: int = 3
  embedding_model: str = "gemini-embedding-001"
  chunk_lines: int = 80
  chunk_overlap_lines: int = 10
  retrieval_top_k: int = 12
  ignore_dirs: set[str] = field(default_factory=lambda: set(DEFAULT_IGNORE_DIRS))
  extensions: set[str] = field(default_factory=lambda: set(DEFAULT_EXTENSIONS))

  def validate(self) -> None:
    if not self.gemini_api_key:
      raise ValueError(
        "GEMINI_API_KEY is not set. Add it to your environment or a .env file."
      )
    if not self.codebase_path.exists():
      raise ValueError(f"Codebase path does not exist: {self.codebase_path}")
    if not self.codebase_path.is_dir():
      raise ValueError(f"Codebase path is not a directory: {self.codebase_path}")
    if self.repeat_interval_seconds < 1:
      raise ValueError("repeat_interval_seconds must be at least 1")
