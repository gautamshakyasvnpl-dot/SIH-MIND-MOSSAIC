import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402

RICH_TEXT = (
    "Photosynthesis converts light energy into chemical energy inside plants. "
    "Chlorophyll is the pigment that captures sunlight in the leaves. "
    "Water and carbon dioxide are the raw materials for this process. "
    "Glucose and oxygen are produced at the end of photosynthesis. "
    "Cellular respiration releases energy from glucose in living cells. "
    "Mitochondria are the organelles where respiration reactions occur. "
    "Oxygen is used during respiration to break down glucose completely. "
    "Carbon dioxide and water are released as waste products of respiration. "
    "Plants perform both photosynthesis and respiration throughout their life. "
    "During daylight hours photosynthesis usually exceeds respiration in rate. "
    "At night only respiration continues because there is no sunlight. "
    "Farmers value both processes when planning crop growth cycles."
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    email = f"w2_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "W2"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def doc_id(client: TestClient, auth: dict[str, str]) -> str:
    files = {"file": ("rich.txt", io.BytesIO(RICH_TEXT.encode()), "text/plain")}
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_ask_grounded_answer_with_sources(
    client: TestClient, auth: dict[str, str], doc_id: str
) -> None:
    r = client.post(
        f"/api/documents/{doc_id}/ask",
        headers=auth,
        json={"question": "What captures sunlight?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["used_llm"] is False
    assert "chlorophyll" in body["answer"].lower()
    assert len(body["sources"]) >= 1
    for src in body["sources"]:
        assert isinstance(src["chunk_index"], int)
        assert set(src) == {"chunk_index", "snippet"}
        assert 0 < len(src["snippet"]) <= 160


def test_task_sprint_lifecycle(
    client: TestClient, auth: dict[str, str]
) -> None:
    r = client.post(
        "/api/tasks",
        headers=auth,
        json={
            "title": "Lab report on photosynthesis",
            "due_date": "2026-09-01",
            "notes": "compare light and dark reactions with examples",
        },
    )
    assert r.status_code == 200, r.text
    task = r.json()
    assert task["status"] == "open"
    assert 3 <= len(task["sprints"]) <= 5
    assert all(s["minutes"] > 0 for s in task["sprints"])

    tid = task["id"]
    sprints = task["sprints"]
    r = client.post(
        f"/api/tasks/{tid}/sprints/{sprints[0]['id']}/toggle", headers=auth
    )
    updated = r.json()
    done_flags = [s["done"] for s in updated["sprints"]]
    assert done_flags[0] is True and not all(done_flags)
    assert updated["status"] == "open"

    for s in sprints[1:]:
        r = client.post(f"/api/tasks/{tid}/sprints/{s['id']}/toggle", headers=auth)
    final = r.json()
    assert final["status"] == "done"

    r = client.delete(f"/api/tasks/{tid}", headers=auth)
    assert r.status_code == 204
    listing = client.get("/api/tasks", headers=auth).json()["items"]
    assert all(t["id"] != tid for t in listing)


def test_viva_full_session(
    client: TestClient, auth: dict[str, str], doc_id: str
) -> None:
    r = client.post(f"/api/documents/{doc_id}/viva/start", headers=auth)
    assert r.status_code == 200, r.text
    start = r.json()
    sid = start["session_id"]
    assert start["turn_count"] == 1
    assert start["question"]

    source_sentences = [
        "Chlorophyll is the pigment that captures sunlight.",
        "Mitochondria are the organelles where respiration reactions occur.",
        "Oxygen is used during respiration to break down glucose completely.",
        "Carbon dioxide is released as a waste product of respiration.",
        "Photosynthesis converts light energy into chemical energy.",
    ]

    for k in range(4):
        r = client.post(f"/api/viva/{sid}/answer", headers=auth, json={"answer": source_sentences[k]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["done"] is False
        assert body["next_question"]
        assert body["turn_count"] == k + 2
        assert body["feedback"]
        assert body["score"] in (0, 1, 2)

    r = client.post(
        f"/api/viva/{sid}/answer", headers=auth, json={"answer": source_sentences[4]}
    )
    assert r.status_code == 200, r.text
    final = r.json()
    assert final["done"] is True
    assert final["next_question"] is None
    assert final["turn_count"] == 5

    transcript = client.get(f"/api/viva/{sid}", headers=auth).json()
    assert transcript["done"] is True
    assert len(transcript["turns"]) == 5
