import os
import time

import httpx

BASE = "http://127.0.0.1:8000"
PDF = os.path.join(os.environ["TEMP"], "attention_paper.pdf")

EMAIL = f"real_{int(time.time())}@test.com"
c = httpx.Client(base_url=BASE, timeout=180)

r = c.post("/api/auth/register", json={"email": EMAIL, "password": "password123", "display_name": "Real"})
h = {"Authorization": f"Bearer {r.json()['token']}"}
print("1 register OK")

with open(PDF, "rb") as f:
    files = {"file": ("attention_is_all_you_need.pdf", f, "application/pdf")}
    r = c.post("/api/documents", headers=h, files=files)
assert r.status_code == 200, r.text
doc = r.json()
print(f"2 upload+extract OK | doc_type={doc['doc_type']} char_count={doc['char_count']}")
assert doc["doc_type"] == "pdf" and doc["char_count"] > 5000, doc

r = c.post(
    f"/api/documents/{doc['id']}/adapt",
    headers=h,
    json={"formats": ["simplified_text", "tts_audio"]},
)
body = r.json()
simp = next(x for x in body["results"] if x["format"] == "simplified_text")
audio = next(x for x in body["results"] if x["format"] == "tts_audio")
print(f"3 adapt | simplified status={simp['status']} len={len(simp['content'] or '')}")
print(f"        tts status={audio['status']} url={audio['content']}")
if simp["status"] == "ok":
    print("   simplified head:", simp["content"][:100].replace("\n", " "))
if audio["status"] == "ok":
    ra = c.get(audio["content"])
    assert ra.status_code == 200 and len(ra.content) > 1000
    print(f"   audio served OK ({len(ra.content)} bytes)")

for q in ["What is the attention mechanism?", "What is multi-head attention?"]:
    r = c.post(f"/api/documents/{doc['id']}/ask", headers=h, json={"question": q})
    assert r.status_code == 200, r.text
    ans = r.json()
    srcs = [(s["chunk_index"], s["snippet"][:50]) for s in ans["sources"]]
    print(f"4 ask OK | Q: {q}")
    print(f"   A ({'LLM' if ans['used_llm'] else 'extractive'}): {ans['answer'][:110]}")
    print(f"   sources: {srcs}")

r = c.get(f"/api/documents/{doc_id}/recommend") if False else c.get(f"/api/documents/{doc['id']}/recommend", headers=h)
rec = r.json()
print(f"5 recommend OK | {rec['format']} - {rec['reason'][:60]}")

r = c.post(f"/api/documents/{doc['id']}/viva/start", headers=h)
if r.status_code == 200:
    sid = r.json()["session_id"]
    q1 = r.json()["question"]
    print(f"6 viva start OK on REAL paper | Q1: {q1[:90]}")
    ra = c.get(f"/api/viva/{sid}/question-audio", headers=h)
    print(f"   question audio: {ra.status_code}, {len(ra.content)} bytes")
    out = c.post(f"/api/viva/{sid}/answer", headers=h,
                 json={"answer": "The Transformer uses attention instead of recurrence."}).json()
    print(f"   first answer graded: score={out['score']} | {out['feedback'][:60]}")
else:
    print(f"6 viva start returned {r.status_code}: {r.text[:120]}")

c.delete(f"/api/documents/{doc['id']}", headers=h)
print("REAL-CONTENT TEST: DONE")
