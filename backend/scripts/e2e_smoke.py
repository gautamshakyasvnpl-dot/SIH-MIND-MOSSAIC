import io
import time

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))
EMAIL = f"e2e_{SUFFIX}@test.com"

c = httpx.Client(base_url=BASE, timeout=60)

r = c.post("/api/auth/register", json={"email": EMAIL, "password": "password123", "display_name": "E2E"})
assert r.status_code == 200, r.text
token = r.json()["token"]
h = {"Authorization": f"Bearer {token}"}
print("1 register OK")

r = c.get("/api/auth/me", headers=h)
assert r.status_code == 200 and r.json()["email"] == EMAIL
print("2 me OK")

r = c.get("/api/profile", headers=h)
assert r.status_code == 200 and r.json()["onboarding_complete"] is False
r = c.put("/api/profile", headers=h, json={"font_style": "dyslexia_friendly", "chunk_size": "small"})
merged = r.json()
assert merged["font_style"] == "dyslexia_friendly" and merged["modality_affinity"] == "text"
print("3 profile create+merge OK")

r = c.post("/api/consents", headers=h, json={"voice": True, "telemetry": False, "memory": True})
assert r.json() == {"voice": True, "telemetry": False, "memory": True}
print("4 consents OK")

text = (
    "Photosynthesis is the process by which green plants make their own food. "
    "They use sunlight, water and carbon dioxide to produce glucose and oxygen. "
    "Chlorophyll inside the leaves captures the light energy. "
    "This energy drives chemical reactions inside the chloroplast. "
    "The oxygen we breathe is a by-product of this process. "
    "Without photosynthesis, most life on Earth could not exist. "
    "Farmers rely on this process to grow crops every single day. "
    "Scientists study it to improve food production worldwide."
)
files = {"file": ("photosynthesis.txt", io.BytesIO(text.encode()), "text/plain")}
r = c.post("/api/documents", headers=h, files=files)
assert r.status_code == 200, r.text
doc = r.json()
assert doc["doc_type"] == "txt" and doc["char_count"] > 100
print("5 upload OK:", doc["id"])

r = c.post(f"/api/documents/{doc['id']}/adapt", headers=h, json={"formats": ["simplified_text", "tts_audio"]})
assert r.status_code == 200, r.text
adapt = r.json()
assert adapt["used_llm"] is False
simplified = next(x for x in adapt["results"] if x["format"] == "simplified_text")
audio = next(x for x in adapt["results"] if x["format"] == "tts_audio")
assert simplified["status"] == "ok" and len(simplified["content"]) > 50
assert audio["status"] == "ok" and audio["content"].startswith("/api/audio/")
print("6 adapt OK | used_llm:", adapt["used_llm"])
print("  simplified head:", simplified["content"][:90].replace("\n", " "))
print("  explanation:", simplified["explanation"][:80])

r = c.get(audio["content"])
assert r.status_code == 200 and r.headers["content-type"].startswith("audio/mpeg") and len(r.content) > 1000
print("7 audio serves OK,", len(r.content), "bytes")

r = c.get("/api/documents", headers=h)
assert any(d["id"] == doc["id"] for d in r.json()["items"])
r = c.delete(f"/api/documents/{doc['id']}", headers=h)
assert r.status_code == 204
print("8 list+delete OK")
print("E2E SMOKE: ALL PASS")
