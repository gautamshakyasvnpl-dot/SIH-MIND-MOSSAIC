import io
import time

import httpx

BASE = "http://127.0.0.1:8000"
EMAIL = f"e2e4_{int(time.time())}@test.com"

c = httpx.Client(base_url=BASE, timeout=60)

r = c.post("/api/auth/register", json={"email": EMAIL, "password": "password123", "display_name": "E2E4"})
h = {"Authorization": f"Bearer {r.json()['token']}"}
print("1 register OK")

TEXT = (
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
doc_id = c.post("/api/documents", headers=h,
                files={"file": ("bio.txt", io.BytesIO(TEXT.encode()), "text/plain")}).json()["id"]

r = c.post(f"/api/documents/{doc_id}/ask", headers=h, json={"question": "What captures sunlight?"})
assert r.status_code == 200 and r.json()["answer"]
print("2 ask OK (TF-IDF fallback path, no key)")

r = c.post(f"/api/documents/{doc_id}/viva/start", headers=h)
sid = r.json()["session_id"]
q = r.json()["question"]
r = c.get(f"/api/viva/{sid}/question-audio", headers=h)
assert r.status_code == 200 and r.headers["content-type"].startswith("audio/mpeg") and len(r.content) > 1000
size_hdr = len(r.content)
cap = c.post("/api/media/token", headers=h, json={"kind": "question_audio", "id": sid}).json()
assert cap["expires_in"] == 60 and cap["url"].startswith("/api/media/")
r2 = c.get(cap["url"])
assert r2.status_code == 200 and len(r2.content) == size_hdr
r3 = c.get(cap["url"])
assert r3.status_code == 200 and len(r3.content) == size_hdr
print("3 question-audio OK via short-lived (60s) signed media token, not single-use (JWT never in URL)")

for i in range(5):
    out = c.post(f"/api/viva/{sid}/answer", headers=h,
                 json={"answer": "Chlorophyll is the pigment that captures sunlight."}).json()
    if out["done"]:
        break

c.put("/api/profile", headers=h, json={"modality_affinity": "text", "chunk_size": "large"})
rec1 = c.get(f"/api/documents/{doc_id}/recommend", headers=h).json()
c.post(f"/api/documents/{doc_id}/adapt", headers=h, json={"formats": ["simplified_text"]})
c.post(f"/api/documents/{doc_id}/adapt", headers=h, json={"formats": ["simplified_text"]})
rec2 = c.get(f"/api/documents/{doc_id}/recommend", headers=h).json()
print("4 recommend before-usage:", rec1["format"], "| after 2x simplified_text usage:", rec2["format"])
assert rec2["format"] == "simplified_text" and "times before" in rec2["reason"], rec2
print("5 usage-aware recommender OK")

c.delete(f"/api/documents/{doc_id}", headers=h)
print("E2E SMOKE V3b: ALL PASS")
