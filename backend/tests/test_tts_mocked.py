from pathlib import Path

import gtts
import pytest

from app.services.tts import synthesize_speech


def _fake_save(self: gtts.gTTS, saveaddr: object) -> None:
    Path(str(saveaddr)).write_bytes(b"ID3MOCK")


def test_synthesize_writes_mock_audio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    out_path = tmp_path / "a.mp3"
    result = synthesize_speech("hello world", out_path)
    assert result == out_path
    assert out_path.exists()
    assert out_path.read_bytes().startswith(b"ID3")
    assert not out_path.with_suffix(".tmp.mp3").exists()


@pytest.mark.parametrize("bad_text", ["", "   ", "\n\t"])
def test_empty_text_raises_runtime_error(tmp_path: Path, bad_text: str) -> None:
    with pytest.raises(RuntimeError):
        synthesize_speech(bad_text, tmp_path / "b.mp3")
