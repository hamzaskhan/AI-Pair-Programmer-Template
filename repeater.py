import time
from datetime import datetime

from config import AppConfig
from notifier import notify_failure, notify_success
from orchestrator import run_analysis


def _print_report(report: str) -> None:
  divider = "=" * 72
  print(f"\n{divider}")
  print("AI Pair Engineer Report")
  print(divider)
  print(report)
  print(f"{divider}\n")


def _run_cycle(config: AppConfig) -> None:
  started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print(f"\n[repeater] Starting analysis cycle at {started}")
  codebase_name = config.codebase_path.name
  try:
    report = run_analysis(config)
    _print_report(report)
    if config.desktop_notify:
      notify_success(codebase_name, report)
  except Exception as exc:
    print(f"[repeater] Analysis failed: {exc}")
    if config.desktop_notify:
      notify_failure(codebase_name, str(exc))
    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or "quota exceeded" in str(exc).lower():
      print(
        "[repeater] Tip: your API key has no free-tier quota for the selected model. "
        "Try `python main.py --once --model gemini-3.1-flash-lite` or check "
        "https://ai.google.dev/gemini-api/docs/rate-limits"
      )


def start(config: AppConfig) -> None:
  config.validate()
  print(
    f"[repeater] Monitoring {config.codebase_path} "
    f"every {config.repeat_interval_seconds}s"
  )

  _run_cycle(config)
  if config.run_once:
    return

  while True:
    time.sleep(config.repeat_interval_seconds)
    _run_cycle(config)
