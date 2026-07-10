import re
import time

from google import genai
from google.genai import types

from baby_agent import SYSTEM_PROMPT, build_user_prompt
from chunkprep import CodeChunk
from config import AppConfig
from vectoriser import VectorStore


def _format_context(chunks: list[CodeChunk]) -> str:
  sections: list[str] = []
  for chunk in chunks:
    sections.append(
      f"### {chunk.label}\n```\n{chunk.content}\n```"
    )
  return "\n\n".join(sections)


def _should_retry_or_fallback(exc: Exception) -> bool:
  message = str(exc)
  return any(
    marker in message
    for marker in ("429", "404", "503", "RESOURCE_EXHAUSTED", "NOT_FOUND", "UNAVAILABLE")
  )


def _retry_delay_seconds(exc: Exception, attempt: int) -> float:
  match = re.search(r"retry in (\d+(?:\.\d+)?)s", str(exc), re.IGNORECASE)
  if match:
    return float(match.group(1)) + 1.0
  return min(60.0, 2.0 ** attempt)


def _model_candidates(config: AppConfig) -> list[str]:
  models = [config.llm_model, *config.llm_fallback_models]
  seen: set[str] = set()
  ordered: list[str] = []
  for model in models:
    if model not in seen:
      seen.add(model)
      ordered.append(model)
  return ordered


class LLMHarness:
  def __init__(self, config: AppConfig):
    self.config = config
    self.client = genai.Client(api_key=config.gemini_api_key)

  def _generate(self, model: str, user_prompt: str) -> str:
    response = self.client.models.generate_content(
      model=model,
      contents=user_prompt,
      config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
      ),
    )
    text = response.text
    if not text:
      raise ValueError("Gemini returned an empty response.")
    return text.strip()

  def analyze(self, vector_store: VectorStore) -> str:
    retrieved = vector_store.search(
      query=(
        "design flaws architecture testing gaps refactoring opportunities "
        "code quality maintainability"
      ),
      top_k=self.config.retrieval_top_k,
    )
    context = _format_context(retrieved)
    user_prompt = build_user_prompt(context)

    last_error: Exception | None = None
    for model in _model_candidates(self.config):
      for attempt in range(1, self.config.llm_max_retries + 1):
        try:
          if model != self.config.llm_model:
            print(f"[llm_harness] Trying fallback model: {model}")
          return self._generate(model, user_prompt)
        except Exception as exc:
          last_error = exc
          if not _should_retry_or_fallback(exc):
            raise
          delay = _retry_delay_seconds(exc, attempt)
          reason = "unavailable" if "503" in str(exc) else "request failed"
          print(
            f"[llm_harness] {model} {reason} "
            f"(attempt {attempt}/{self.config.llm_max_retries}). "
            f"Retrying in {delay:.0f}s..."
          )
          time.sleep(delay)

    raise RuntimeError(
      "Gemini could not complete the request for any configured model. "
      "Try `python main.py --once --model gemini-3.1-flash-lite` or set "
      "GEMINI_MODEL in your .env file."
    ) from last_error
