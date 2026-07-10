import sys


def _truncate(text: str, limit: int = 220) -> str:
  collapsed = " ".join(text.split())
  if len(collapsed) <= limit:
    return collapsed
  return collapsed[: limit - 3] + "..."


def _notify_winotify(title: str, message: str) -> None:
  from winotify import Notification

  toast = Notification(
    app_id="AI Pair Engineer",
    title=title,
    msg=message,
    duration="long",
  )
  toast.show()


def _notify_message_box(title: str, message: str) -> None:
  import ctypes

  ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
    0,
    message,
    title,
    0x40,  # MB_ICONINFORMATION
  )


def notify_desktop(title: str, message: str) -> None:
  if sys.platform != "win32":
    print(f"[notifier] Skipping desktop notification on {sys.platform}")
    return

  try:
    _notify_winotify(title, message)
    return
  except Exception as exc:
    print(f"[notifier] Toast failed ({exc}), falling back to message box...")
    _notify_message_box(title, message)


def notify_success(codebase_name: str, report: str) -> None:
  notify_desktop(
    title=f"AI Pair Engineer — {codebase_name}",
    message=_truncate(report),
  )


def notify_failure(codebase_name: str, error: str) -> None:
  notify_desktop(
    title=f"AI Pair Engineer failed — {codebase_name}",
    message=_truncate(error),
  )
