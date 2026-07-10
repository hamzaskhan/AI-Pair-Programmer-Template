from dataclasses import dataclass

import numpy as np
from google import genai
from google.genai import types

from chunkprep import CodeChunk
from config import AppConfig


@dataclass
class IndexedChunk:
  chunk: CodeChunk
  embedding: list[float]


class VectorStore:
  def __init__(self, config: AppConfig):
    self.config = config
    self.client = genai.Client(api_key=config.gemini_api_key)
    self.items: list[IndexedChunk] = []

  def _embed_texts(self, texts: list[str]) -> list[list[float]]:
    if not texts:
      return []

    response = self.client.models.embed_content(
      model=self.config.embedding_model,
      contents=texts,
      config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )

    embeddings: list[list[float]] = []
    for item in response.embeddings:
      values = getattr(item, "values", None)
      if values is None and isinstance(item, dict):
        values = item.get("values")
      if values is None:
        raise ValueError("Embedding response did not include vector values.")
      embeddings.append(list(values))
    return embeddings

  def index_chunks(self, chunks: list[CodeChunk]) -> None:
    self.items = []
    batch_size = 32
    for start in range(0, len(chunks), batch_size):
      batch = chunks[start : start + batch_size]
      texts = [chunk.content for chunk in batch]
      vectors = self._embed_texts(texts)
      for chunk, vector in zip(batch, vectors, strict=True):
        self.items.append(IndexedChunk(chunk=chunk, embedding=vector))

  def _embed_query(self, query: str) -> np.ndarray:
    response = self.client.models.embed_content(
      model=self.config.embedding_model,
      contents=query,
      config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    values = response.embeddings[0].values
    return np.array(values, dtype=np.float32)

  @staticmethod
  def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = query / (np.linalg.norm(query) + 1e-10)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return matrix_norm @ query_norm

  def search(self, query: str, top_k: int) -> list[CodeChunk]:
    if not self.items:
      return []

    query_vector = self._embed_query(query)
    matrix = np.array([item.embedding for item in self.items], dtype=np.float32)
    scores = self._cosine_similarity(query_vector, matrix)
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    return [self.items[index].chunk for index in ranked_indices]
