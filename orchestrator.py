from config import AppConfig
from chunkprep import chunk_codebase
from llm_harness import LLMHarness
from vectoriser import VectorStore


def run_analysis(config: AppConfig) -> str:
  print(f"[orchestrator] Loading codebase from {config.codebase_path}")
  chunks = chunk_codebase(config.codebase_path, config)
  print(f"[orchestrator] Created {len(chunks)} chunks")

  vector_store = VectorStore(config)
  print("[orchestrator] Vectorising chunks with Gemini embeddings...")
  vector_store.index_chunks(chunks)
  print(f"[orchestrator] Indexed {len(vector_store.items)} vectors")

  harness = LLMHarness(config)
  print("[orchestrator] Sending retrieved context to Gemini...")
  return harness.analyze(vector_store)
