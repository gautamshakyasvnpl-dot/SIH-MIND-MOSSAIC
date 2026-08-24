import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  adaptDocument,
  fetchProtectedMediaBlobUrl,
  getAdaptations,
  getDocument,
  getProfile,
  getRecommendation,
  mediaUrl,
  type AdaptResponse,
  type AdaptResult,
  type DocumentMeta,
  type RecommendOut,
} from "../lib/api";
import { useSensorySettings } from "../context/SensorySettings";
import AskPanel from "../components/AskPanel";
import ConceptMap from "../components/ConceptMap";
import { usePageTitle } from "../hooks/usePageTitle";

function findResult(results: AdaptResult[], format: string): AdaptResult | undefined {
  return results.find((r) => r.format === format);
}

export default function DocumentView() {
  const { id } = useParams();
  const { prefs } = useSensorySettings();
  const [doc, setDoc] = useState<DocumentMeta | null>(null);
  const [result, setResult] = useState<AdaptResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendOut | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [showOriginal, setShowOriginal] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileBusy, setFileBusy] = useState(false);
  const [fileNote, setFileNote] = useState("");

  usePageTitle(doc?.filename ?? "Document");

  useEffect(
    () => () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    },
    [previewUrl]
  );

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setLoadError("");
    setStatus("");
    setDoc(null);
    setResult(null);
    setShowOriginal(false);
    getDocument(id)
      .then((d) => {
        if (!cancelled) setDoc(d);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if ((err as Error & { status?: number })?.status === 404) setNotFound(true);
        else setLoadError(err instanceof Error ? err.message : "Could not load document");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    getAdaptations(id)
      .then((r) => {
        if (!cancelled && r?.results?.length) setResult(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getRecommendation(id)
      .then((r) => {
        if (!cancelled) setRecommendation(r);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function onAdapt() {
    if (!id) return;
    setBusy(true);
    setStatus("Adapting your document… this can take a few seconds.");
    try {
      await getProfile();
      const res = await adaptDocument(id);
      setResult(res);
      const failed = res.results.some((r) => r.status === "error");
      setStatus(
        failed
          ? "Finished, but some parts could not be prepared — details below."
          : "Done. Simplified text and audio are ready below."
      );
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Adaptation failed");
    } finally {
      setBusy(false);
    }
  }

  async function downloadOriginal() {
    if (!id || fileBusy) return;
    setFileBusy(true);
    setFileNote("Preparing your file…");
    try {
      const url = await fetchProtectedMediaBlobUrl("document_file", id);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = doc?.filename || "original-file";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setFileNote("");
    } catch (err) {
      setFileNote(err instanceof Error ? err.message : "Could not prepare the original file");
    } finally {
      setFileBusy(false);
    }
  }

  async function toggleOriginal() {
    if (!id || fileBusy) return;
    if (showOriginal) {
      setShowOriginal(false);
      setPreviewUrl(null);
      setFileNote("");
      return;
    }
    setShowOriginal(true);
    setFileBusy(true);
    setFileNote("");
    try {
      setPreviewUrl(await fetchProtectedMediaBlobUrl("document_file", id));
    } catch (err) {
      setFileNote(err instanceof Error ? err.message : "Could not load the original file");
    } finally {
      setFileBusy(false);
    }
  }

  if (loading) {
    return (
      <main id="main" tabIndex={-1}>
        <h1 className="page-title" tabIndex={-1}>Document</h1>
        <p role="status" aria-live="polite">Loading your document…</p>
      </main>
    );
  }

  if (notFound || !doc) {
    return (
      <main id="main" tabIndex={-1}>
        <h1 className="page-title" tabIndex={-1}>Document</h1>
        <p role="alert" aria-live="polite">
          {notFound
            ? "We couldn't find that document in your library."
            : loadError || "We couldn't load that document."}
        </p>
        <p>
          <Link to="/library">Back to your library</Link>
        </p>
      </main>
    );
  }

  const isPdf = doc.doc_type.toLowerCase() === "pdf";
  const simplified = result ? findResult(result.results, "simplified_text") : undefined;
  const audio = result ? findResult(result.results, "tts_audio") : undefined;
  const conceptMap = result ? findResult(result.results, "concept_map") : undefined;
  const failedResults = result
    ? result.results.filter((r) => r.status === "error" && r.format !== "simplified_text" && r.format !== "tts_audio")
    : [];

  return (
    <main id="main" tabIndex={-1}>
      <h1 className="page-title" tabIndex={-1}>{doc.filename}</h1>
      <p>
        <button type="button" onClick={() => void downloadOriginal()} disabled={fileBusy}>
          Download original file
        </button>{" "}
        ·{" "}
        <button type="button" onClick={() => void toggleOriginal()} disabled={fileBusy}>
          {showOriginal ? "Hide" : "View"} original here
        </button>
      </p>
      <p role="status" aria-live="polite">
        {fileBusy ? "Preparing your file…" : fileNote}
      </p>
      {showOriginal && (
        <section aria-labelledby="original-heading">
          <h2 id="original-heading">Original document</h2>
          {isPdf ? (
            previewUrl ? (
              <iframe
                src={previewUrl}
                title="Original PDF preview"
                width="100%"
                height="520"
                style={{ border: "1px solid var(--color-line)", borderRadius: "var(--radius)" }}
              />
            ) : (
              <p role="status" aria-live="polite">
                <small>Loading PDF preview…</small>
              </p>
            )
          ) : (
            <p>
              <small>
                Inline preview is only available for PDFs. Use the download button above —
                Office files will download.
              </small>
            </p>
          )}
        </section>
      )}
      {recommendation && (
        <p role="note" className="recommend-chip">
          <strong>Recommended: {recommendation.format}</strong>{" "}
          <small>{recommendation.reason}</small>
        </p>
      )}
      <button type="button" onClick={() => void onAdapt()} disabled={busy}>
        {busy ? "Working…" : result ? "Re-adapt" : "Adapt for me"}
      </button>
      <p role="status" aria-live="polite">
        {status}
      </p>
      {conceptMap?.content && (
        <section aria-labelledby="map-heading">
          <h2 id="map-heading">Concept map</h2>
          <ConceptMap src={String(conceptMap.content)} />
          {conceptMap.explanation && (
            <p>
              <small>Why this map: {conceptMap.explanation}</small>
            </p>
          )}
        </section>
      )}
      {simplified && simplified.status === "error" && (
        <section aria-labelledby="simplified-heading">
          <h2 id="simplified-heading">Simplified text</h2>
          <p role="note">
            The simplified text could not be prepared this time.
            {simplified.explanation ? ` ${simplified.explanation}` : ""} You can try
            adapting again in a moment.
          </p>
        </section>
      )}
      {simplified && simplified.status !== "error" && simplified.content && (
        <section aria-labelledby="simplified-heading">
          <h2 id="simplified-heading">Simplified text</h2>
          <article className="prose">
            {String(simplified.content).split(/\n{2,}/).map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </article>
          {simplified.explanation && (
            <p>
              <small>Why this rendering: {simplified.explanation}</small>
            </p>
          )}
        </section>
      )}
      {audio && audio.status === "error" && (
        <section aria-labelledby="audio-heading">
          <h2 id="audio-heading">Listen</h2>
          <p role="note">
            The audio version could not be prepared this time.
            {audio.explanation ? ` ${audio.explanation}` : ""} The simplified text above
            is still available, and you can try again.
          </p>
        </section>
      )}
      {audio && audio.status !== "error" && audio.content && (
        <section aria-labelledby="audio-heading">
          <h2 id="audio-heading">Listen</h2>
          <audio
            controls
            preload="none"
            src={mediaUrl(String(audio.content))}
            autoPlay={prefs.audio_autoplay}
          />
          {audio.explanation && (
            <p>
              <small>Why this format: {audio.explanation}</small>
            </p>
          )}
        </section>
      )}
      {failedResults.map((r) => (
        <p key={r.format} role="note">
          {r.format} could not be prepared.
          {r.explanation ? ` ${r.explanation}` : ""}
        </p>
      ))}
      {result?.used_llm === false && (
        <p>
          <small>Generated offline (heuristic mode) — no AI key configured.</small>
        </p>
      )}
      <AskPanel docId={id ?? ""} />
      <p>
        <Link to={`/document/${id}/viva`}>Practice a viva on this document →</Link>
      </p>
    </main>
  );
}
