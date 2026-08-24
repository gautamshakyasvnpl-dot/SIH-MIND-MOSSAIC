import io
import time

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))
EMAIL = f"e2e2_{SUFFIX}@test.com"

c = httpx.Client(base_url=BASE, timeout=60)

r = c.post("/api/auth/register", json={"email": EMAIL, "password": "password123", "display_name": "E2E2"})
token = r.json()["token"]
h = {"Authorization": f"Bearer {token}"}
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
r = c.post("/api/documents", headers=h,
           files={"file": ("bio.txt", io.BytesIO(TEXT.encode()), "text/plain")})
doc_id = r.json()["id"]
print("2 upload OK", doc_id[:8])

r = c.post(f"/api/documents/{doc_id}/ask", headers=h,
           json={"question": "What captures sunlight?"})
body = r.json()
assert body["answer"], r.text
assert len(body["sources"]) >= 1 and "chunk_index" in body["sources"][0]
assert body["used_llm"] is False
print("3 ask OK | answer:", body["answer"][:80].replace("\n", " "))
print("   sources:", [(s['chunk_index'], s['snippet'][:40] + 'â€¦') for s in body['sources']])

r = c.post("/api/tasks", headers=h,
           json={"title": "Lab report on photosynthesis",
                 "due_date": "2026-09-01",
                 "notes": "compare light and dark reactions"})
task = r.json()
assert 3 <= len(task["sprints"]) <= 5 and task["status"] == "open"
print("4 task OK | sprints:", [(s['description'], s['minutes']) for s in task['sprints']])

tid = task["id"]
for s in task["sprints"]:
    r = c.post(f"/api/tasks/{tid}/sprints/{s['id']}/toggle", headers=h)
final = r.json()
assert final["status"] == "done"
r = c.delete(f"/api/tasks/{tid}", headers=h)
assert r.status_code == 204
print("5 sprint toggleâ†’doneâ†’delete OK")

r = c.post(f"/api/documents/{doc_id}/viva/start", headers=h)
start = r.json()
sid = start["session_id"]
assert start["turn_count"] == 1 and start["question"]
print("6 viva start OK | Q1:", start["question"][:70])

answers = [
    "Chlorophyll is the pigment that captures sunlight.",
    "Mitochondria are the organelles where respiration reactions occur.",
    "Oxygen is used to break down glucose.",
    "Carbon dioxide is released as a waste product of respiration.",
    "Photosynthesis converts light energy into chemical energy.",
]
done = False
i = 0
while not done and i < 6:
    r = c.post(f"/api/viva/{sid}/answer", headers=h, json={"answer": answers[i % 5]})
    out = r.json()
    i += 1
    done = out["done"]
    if not done:
        assert out["next_question"]
print(f"7 viva answered x{i} â†’ done={done}")

r = c.get(f"/api/viva/{sid}", headers=h)
tr = r.json()
scores = [t["score"] for t in tr["turns"]]
assert tr["done"] is True and len(tr["turns"]) >= 5
print("8 transcript OK | scores:", scores)
c.delete(f"/api/documents/{doc_id}", headers=h)
print("E2E SMOKE V2: ALL PASS")

