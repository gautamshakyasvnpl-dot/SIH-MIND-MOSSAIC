import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, password: str = "password123") -> dict[str, str]:
    email = f"contract_{uuid.uuid4().hex[:10]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "display_name": "C"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _grant(client: TestClient, headers: dict[str, str], **flags: bool) -> None:
    r = client.post("/api/consents", headers=headers, json=flags)
    assert r.status_code == 200, r.text


def test_register_normalizes_email_and_returns_shape(client: TestClient) -> None:
    email = f"Norm_{uuid.uuid4().hex[:8]}@Example.COM"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Str0ngPass!", "display_name": "N"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"token", "user"}
    assert set(body["user"]) == {"id", "email", "display_name"}
    assert body["user"]["email"] == email.strip().lower()


def test_login_happy_path_with_case_and_whitespace(client: TestClient) -> None:
    email = f"login_{uuid.uuid4().hex[:8]}@Test.com"
    registered = client.post(
        "/api/auth/login",
        json={"email": email, "password": "whatever1"},
    )
    assert registered.status_code == 401
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "Str0ngPass!", "display_name": "L"},
    )
    r = client.post(
        "/api/auth/login",
        json={"email": f"  {email.upper()} ", "password": "Str0ngPass!"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"token", "user"}
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}).json()
    assert set(me) == {"id", "email", "display_name"}
    assert me["email"] == email.lower()


def test_duplicate_registration_different_case_409(client: TestClient) -> None:
    email = f"dupe_{uuid.uuid4().hex[:8]}@test.com"
    first = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Str0ngPass!", "display_name": "D"},
    )
    assert first.status_code == 200, first.text
    second = client.post(
        "/api/auth/register",
        json={"email": email.upper(), "password": "Another123!", "display_name": "D2"},
    )
    assert second.status_code == 409, second.text
    assert "detail" in second.json()


def test_login_invalid_credentials_401(client: TestClient) -> None:
    email = f"invalid_{uuid.uuid4().hex[:8]}@test.com"
    registered = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Str0ngPass!", "display_name": "I"},
    )
    assert registered.status_code == 200, registered.text
    wrong_password = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPass9"},
    )
    assert wrong_password.status_code == 401
    unknown_email = client.post(
        "/api/auth/login",
        json={"email": f"nobody_{uuid.uuid4().hex[:6]}@test.com", "password": "whatever1"},
    )
    assert unknown_email.status_code == 401


def test_register_short_password_422(client: TestClient) -> None:
    short = client.post(
        "/api/auth/register",
        json={"email": f"short_{uuid.uuid4().hex[:6]}@test.com", "password": "  ab12  ", "display_name": "S"},
    )
    assert short.status_code == 422, short.text
    seven = client.post(
        "/api/auth/register",
        json={"email": f"seven_{uuid.uuid4().hex[:6]}@test.com", "password": "abcdefg", "display_name": "S"},
    )
    assert seven.status_code == 422, seven.text
    eight = client.post(
        "/api/auth/register",
        json={"email": f"eight_{uuid.uuid4().hex[:6]}@test.com", "password": " abcdefgh", "display_name": "S"},
    )
    assert eight.status_code == 200, eight.text


def test_legacy_user_with_short_password_can_still_login(client: TestClient) -> None:
    from app.core.security import hash_password
    from app.db import SessionLocal
    from app.models import User

    email = f"legacy_{uuid.uuid4().hex[:8]}@test.com"
    password = "seven6x"
    db = SessionLocal()
    try:
        db.add(User(email=email, display_name="Legacy", password_hash=hash_password(password)))
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["email"] == email


def test_register_invalid_email_422(client: TestClient) -> None:
    for bad in ("", "   ", "not-an-email"):
        r = client.post(
            "/api/auth/register",
            json={"email": bad, "password": "Str0ngPass!", "display_name": "E"},
        )
        assert r.status_code == 422, (bad, r.text)


def test_put_profile_explicit_null_rejected_422(client: TestClient) -> None:
    headers = _register(client)
    for payload in (
        {"pace": None},
        {"reduce_motion": None},
        {"modality_affinity": None},
        {"onboarding_complete": None},
    ):
        r = client.put("/api/profile", headers=headers, json=payload)
        assert r.status_code == 422, (payload, r.text)


def test_put_profile_partial_merge_preserves_fields(client: TestClient) -> None:
    headers = _register(client)
    r = client.put("/api/profile", headers=headers, json={"font_style": "dyslexia_friendly"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["font_style"] == "dyslexia_friendly"
    assert body["chunk_size"] == "medium"
    assert body["onboarding_complete"] is False
    second = client.put(
        "/api/profile", headers=headers, json={"onboarding_complete": True}
    )
    assert second.status_code == 200, second.text
    merged = second.json()
    assert merged["onboarding_complete"] is True
    assert merged["font_style"] == "dyslexia_friendly"
    fetched = client.get("/api/profile", headers=headers).json()
    assert fetched == merged


def test_put_profile_bad_enum_values_422(client: TestClient) -> None:
    headers = _register(client)
    for payload in (
        {"modality_affinity": "kinesthetic"},
        {"chunk_size": "huge"},
        {"font_style": "comic_sans"},
        {"line_spacing": "double"},
        {"pace": "fast"},
    ):
        r = client.put("/api/profile", headers=headers, json=payload)
        assert r.status_code == 422, (payload, r.text)


def test_put_profile_strict_booleans_422(client: TestClient) -> None:
    headers = _register(client)
    for payload in (
        {"reduce_motion": "yes"},
        {"audio_autoplay": 1},
        {"noise_sensitive": "false"},
        {"onboarding_complete": 0},
    ):
        r = client.put("/api/profile", headers=headers, json=payload)
        assert r.status_code == 422, (payload, r.text)


def test_put_profile_valid_values_accepted(client: TestClient) -> None:
    headers = _register(client)
    r = client.put(
        "/api/profile",
        headers=headers,
        json={
            "modality_affinity": "audio",
            "chunk_size": "small",
            "line_spacing": "wide",
            "reduce_motion": True,
            "pace": "gentle",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["modality_affinity"] == "audio"
    assert body["chunk_size"] == "small"
    assert body["line_spacing"] == "wide"
    assert body["reduce_motion"] is True
    assert body["pace"] == "gentle"


def test_consents_non_bool_rejected_422(client: TestClient) -> None:
    headers = _register(client)
    for payload in (
        {"voice": "true"},
        {"telemetry": 1},
        {"memory": "yes"},
    ):
        r = client.post("/api/consents", headers=headers, json=payload)
        assert r.status_code == 422, (payload, r.text)


def test_consents_merge_preserves_omitted_keys(client: TestClient) -> None:
    headers = _register(client)
    r = client.post("/api/consents", headers=headers, json={"voice": True})
    assert r.status_code == 200, r.text
    assert r.json() == {"voice": True, "telemetry": False, "memory": False}

    r = client.post("/api/consents", headers=headers, json={"telemetry": True})
    assert r.status_code == 200, r.text
    assert r.json() == {"voice": True, "telemetry": True, "memory": False}

    r = client.post("/api/consents", headers=headers, json={})
    assert r.status_code == 200, r.text
    assert r.json() == {"voice": True, "telemetry": True, "memory": False}

    r = client.post("/api/consents", headers=headers, json={"voice": False})
    assert r.status_code == 200, r.text
    assert r.json() == {"voice": False, "telemetry": True, "memory": False}

    fetched = client.get("/api/consents", headers=headers).json()
    assert fetched == {"voice": False, "telemetry": True, "memory": False}


def test_consents_explicit_null_rejected_422(client: TestClient) -> None:
    headers = _register(client)
    _grant(client, headers, voice=True)

    r = client.post("/api/consents", headers=headers, json={"voice": None})
    assert r.status_code == 422, r.text

    for payload in (
        {"telemetry": None},
        {"memory": None},
        {"voice": True, "memory": None},
    ):
        denied = client.post("/api/consents", headers=headers, json=payload)
        assert denied.status_code == 422, (payload, denied.text)

    fetched = client.get("/api/consents", headers=headers).json()
    assert fetched == {"voice": True, "telemetry": False, "memory": False}


def test_stt_gated_by_voice_consent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    headers = _register(client)

    denied = client.post(
        "/api/stt",
        headers=headers,
        files={"file": ("note.webm", b"RIFFfakeaudio", "audio/webm")},
    )
    assert denied.status_code == 403, denied.text
    detail = denied.json()["detail"]
    assert "consent settings" in detail and "voice" in detail.lower()

    _grant(client, headers, voice=True)
    allowed = client.post(
        "/api/stt",
        headers=headers,
        files={"file": ("note.webm", b"RIFFfakeaudio", "audio/webm")},
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json() == {"text": "", "engine": ""}


def test_interactions_gated_by_telemetry_consent(client: TestClient) -> None:
    headers = _register(client)

    denied = client.post(
        "/api/interactions", headers=headers, json={"event": "feedback_too_long"}
    )
    assert denied.status_code == 403, denied.text
    assert "consent settings" in denied.json()["detail"]

    alias_denied = client.post(
        "/api/feedback", headers=headers, json={"event": "requested_example"}
    )
    assert alias_denied.status_code == 403, alias_denied.text

    _grant(client, headers, telemetry=True)
    allowed = client.post(
        "/api/interactions", headers=headers, json={"event": "feedback_too_long"}
    )
    assert allowed.status_code == 200, allowed.text
    scores = allowed.json()["scores"]
    assert scores["short_explanations"] > 0.5


def test_memory_surface_gated_by_memory_consent(client: TestClient) -> None:
    headers = _register(client)

    denied = client.get("/api/preferences/memory", headers=headers)
    assert denied.status_code == 403, denied.text
    assert "consent settings" in denied.json()["detail"]

    _grant(client, headers, memory=True)
    allowed = client.get("/api/preferences/memory", headers=headers)
    assert allowed.status_code == 200, allowed.text
    body = allowed.json()
    assert set(body) == {"struggled_concepts", "suggestions"}

    explicit_false = _register(client)
    _grant(client, explicit_false, memory=False)
    still_denied = client.get("/api/preferences/memory", headers=explicit_false)
    assert still_denied.status_code == 403
    assert client.get("/api/consents", headers=explicit_false).json()["memory"] is False


def test_ungated_routes_work_without_consent(client: TestClient) -> None:
    headers = _register(client)
    assert client.get("/api/profile", headers=headers).status_code == 200
    put = client.put("/api/profile", headers=headers, json={"pace": "gentle"})
    assert put.status_code == 200
    assert client.get("/api/consents", headers=headers).status_code == 200
    checkin = client.post("/api/checkins", headers=headers, json={"mood": 3})
    assert checkin.status_code == 200, checkin.text
    prefs = client.get("/api/preferences", headers=headers)
    assert prefs.status_code == 200
