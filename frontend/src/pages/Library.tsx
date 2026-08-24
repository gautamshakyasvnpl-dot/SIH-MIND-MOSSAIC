import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
  uploadImageOcr,
  type DocumentMeta,
} from "../lib/api";
import { usePageTitle } from "../hooks/usePageTitle";

export default function Library() {
  const [docs, setDocs] = useState<DocumentMeta[] | null>(null);
  const [status, setStatus] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const photoRef = useRef<HTMLInputElement>(null);

  usePageTitle("Library");

  const refresh = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocs(res.items);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not load documents");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onUpload() {
    if (!file) return;
    setStatus("Uploading…");
    try {
      await uploadDocument(file);
      setStatus("Upload complete.");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function onPhotoUpload() {
    if (!photo) return;
    setStatus("Reading the photo…");
    try {
      const meta = await uploadImageOcr(photo);
      setStatus(`Extracted ${meta.char_count} characters from ${meta.filename}.`);
      setPhoto(null);
      if (photoRef.current) photoRef.current.value = "";
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not read that image");
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Delete this document?")) return;
    try {
      await deleteDocument(id);
      await refresh();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>Your document library</h1>
      <section aria-labelledby="upload-heading">
        <h2 id="upload-heading">Add a lecture file</h2>
        <p>
          <label htmlFor="file">Choose a lecture file (.pptx, .pdf, .docx, .txt)</label>
          <br />
          <input
            ref={fileRef}
            id="file"
            type="file"
            accept=".pptx,.pdf,.docx,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </p>
        <button type="button" onClick={onUpload} disabled={!file}>
          Upload
        </button>
        <p>
          <label htmlFor="photo">Or upload a photo of handwritten notes (needs AI key)</label>
          <br />
          <input
            ref={photoRef}
            id="photo"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
          />
        </p>
        <button type="button" onClick={onPhotoUpload} disabled={!photo}>
          Extract text from photo
        </button>
      </section>
      <p role="status" aria-live="polite">
        {status}
      </p>
      {docs === null ? (
        <p>Loading…</p>
      ) : docs.length === 0 ? (
        <p>No documents yet. Upload your first lecture file above.</p>
      ) : (
        <ul className="doc-list card">
          {docs.map((d) => (
            <li key={d.id} className="doc-row">
              <Link to={`/document/${d.id}`}>{d.filename}</Link>{" "}
              <span className="stamp">{d.doc_type}</span>{" "}
              <span className="doc-date">{new Date(d.created_at).toLocaleDateString()}</span>{" "}
              <button type="button" onClick={() => onDelete(d.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
