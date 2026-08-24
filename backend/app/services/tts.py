import os
import threading
from pathlib import Path

from gtts import gTTS


def synthesize_speech(text: str, out_path: Path) -> Path:
    """Write MP3 to out_path (gTTS). Raise RuntimeError on failure."""
    if not text.strip():
        raise RuntimeError("cannot synthesize empty text")
    tmp_path = out_path.with_suffix(".tmp.mp3")
    try:
        gTTS(text=text, lang="en").save(str(tmp_path))
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(str(exc)) from exc
    os.replace(tmp_path, out_path)
    return out_path


def synthesize_speech_bounded(
    text: str,
    out_path: Path,
    max_words: int = 220,
    timeout_s: float = 30.0,
) -> Path:
    """Length-capped synthesis with a hard wall-clock bound.

    Returns the written path on success; raises RuntimeError when gTTS fails
    or exceeds timeout_s, so request paths can degrade gracefully instead of
    hanging on a stalled network call.
    """
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
    outcome: dict[str, object] = {}

    def _work() -> None:
        try:
            outcome["path"] = synthesize_speech(text, out_path)
        except Exception as exc:
            outcome["error"] = exc

    worker = threading.Thread(target=_work, daemon=True)
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        raise RuntimeError("text-to-speech took too long; try again or read the text")
    error = outcome.get("error")
    if isinstance(error, BaseException):
        raise RuntimeError(str(error)) from error
    path = outcome.get("path")
    if not isinstance(path, Path):
        raise RuntimeError("text-to-speech produced no output")
    return path
