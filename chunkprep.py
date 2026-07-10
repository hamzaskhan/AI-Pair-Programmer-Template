from dataclasses import dataclass
from pathlib import Path

from config import AppConfig


@dataclass(frozen=True)
class CodeChunk:
  file_path: str
  content: str
  start_line: int
  end_line: int

  @property
  def label(self) -> str:
    return f"{self.file_path}:{self.start_line}-{self.end_line}"


def _should_skip(path: Path, config: AppConfig) -> bool:
  return any(part in config.ignore_dirs for part in path.parts)


def collect_source_files(root: Path, config: AppConfig) -> list[Path]:
  files: list[Path] = []
  for path in root.rglob("*"):
    if not path.is_file():
      continue
    if _should_skip(path.relative_to(root), config):
      continue
    if path.suffix.lower() not in config.extensions:
      continue
    files.append(path)
  return sorted(files)


def _chunk_file_lines(
  lines: list[str],
  file_path: str,
  chunk_lines: int,
  overlap_lines: int,
) -> list[CodeChunk]:
  if not lines:
    return []

  chunks: list[CodeChunk] = []
  step = max(1, chunk_lines - overlap_lines)
  for start in range(0, len(lines), step):
    end = min(start + chunk_lines, len(lines))
    chunk_text = "".join(lines[start:end]).rstrip()
    if chunk_text:
      chunks.append(
        CodeChunk(
          file_path=file_path,
          content=chunk_text,
          start_line=start + 1,
          end_line=end,
        )
      )
    if end >= len(lines):
      break
  return chunks


def chunk_codebase(root: Path, config: AppConfig) -> list[CodeChunk]:
  chunks: list[CodeChunk] = []
  for file_path in collect_source_files(root, config):
    relative = file_path.relative_to(root).as_posix()
    try:
      text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
      continue
    lines = text.splitlines(keepends=True)
    chunks.extend(
      _chunk_file_lines(
        lines,
        relative,
        config.chunk_lines,
        config.chunk_overlap_lines,
      )
    )
  return chunks
