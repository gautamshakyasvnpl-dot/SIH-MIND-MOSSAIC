import time

import httpx

BASE = "http://127.0.0.1:8000"
EMAIL = f"e2e3_{int(time.time())}@test.com"

c = httpx.Client(base_url=BASE, timeout=60)

r = c.post("/api/auth/register", json={"email": EMAIL, "password": "password123", "display_name": "E2E3"})
h = {"Authorization": f"Bearer {r.json()['token']}"}
print("1 register OK")

r = c.post("/api/checkins", headers=h, json={"mood": 1, "note": None})
body = r.json()
sug = body["suggestion"].lower()
assert "box breathing" in sug, body
assert "counselling" in sug, body
print("2 checkin low-mood OK | suggestion:", body["suggestion"][:70], "...")

r = c.get("/api/checkins", headers=h)
items = r.json()["items"]
assert len(items) == 1 and items[0]["id"] == body["id"]

c.put("/api/profile", headers=h, json={"modality_affinity": "audio"})
import io
files = {"file": ("x.txt", io.BytesIO(("Photosynthesis captures sunlight. " * 30).encode()), "text/plain")}
doc_id = c.post("/api/documents", headers=h, files=files).json()["id"]
r = c.get(f"/api/documents/{doc_id}/recommend", headers=h)
rec = r.json()
assert rec["format"] == "audio" and rec["reason"], rec
print("3 recommend OK |", rec["format"], "-", rec["reason"][:60], "...")

r = c.post("/api/stt", headers=h, files={"file": ("a.webm", b"RIFFfake", "audio/webm")})
assert r.status_code == 200 and r.json() == {"text": "", "engine": ""}, r.text
print("4 stt-no-key OK |", r.json())

c.delete(f"/api/documents/{doc_id}", headers=h)
print("E2E SMOKE V3: ALL PASS")
