export const API_BASE: string =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";

const BASE = API_BASE;

export const SESSION_EXPIRED_EVENT = "neurolearn:session-expired";

const PUBLIC_PATHS = new Set(["/", "/landing", "/login", "/register"]);

export function getToken(): string | null {
  return localStorage.getItem("sahaik_token");
}

export function setToken(token: string): void {
  localStorage.setItem("sahaik_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("sahaik_token");
}

function handleUnauthorizedResponse(): void {
  clearToken();
  if (PUBLIC_PATHS.has(window.location.pathname)) return;
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  for (const [k, v] of Object.entries(authHeaders())) headers.set(k, v);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // non-JSON error body
    }
    if (res.status === 401) handleUnauthorizedResponse();
    const err: Error & { status?: number } = new Error(detail);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export type User = { id: string; email: string; display_name: string };
export type AuthResponse = { token: string; user: User };
export type Profile = {
  modality_affinity: "text" | "audio" | "visual";
  chunk_size: "small" | "medium" | "large";
  font_style: "default" | "dyslexia_friendly";
  line_spacing: "normal" | "wide";
  reduce_motion: boolean;
  audio_autoplay: boolean;
  pace: "gentle" | "standard";
  noise_sensitive: boolean;
  onboarding_complete: boolean;
};
export type Consents = { voice: boolean; telemetry: boolean; memory: boolean };
export type DocumentMeta = {
  id: string;
  filename: string;
  doc_type: string;
  char_count: number;
  created_at: string;
};
export type AdaptResult = {
  format: string;
  status: string;
  content: string | null;
  explanation: string;
};
export type AdaptResponse = {
  document_id: string;
  used_llm: boolean;
  results: AdaptResult[];
};

export const register = (email: string, password: string, display_name: string) =>
  apiFetch<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name }),
  });

export const login = (email: string, password: string) =>
  apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const getMe = () => apiFetch<User>("/api/auth/me");

export const getProfile = () => apiFetch<Profile>("/api/profile");

export const putProfile = (partial: Partial<Profile>) =>
  apiFetch<Profile>("/api/profile", {
    method: "PUT",
    body: JSON.stringify(partial),
  });

export const getConsents = () => apiFetch<Consents>("/api/consents");

export const putConsents = (c: Consents) =>
  apiFetch<Consents>("/api/consents", {
    method: "POST",
    body: JSON.stringify(c),
  });

export const listDocuments = () =>
  apiFetch<{ items: DocumentMeta[] }>("/api/documents");

export const uploadDocument = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return apiFetch<DocumentMeta>("/api/documents", { method: "POST", body: fd });
};

export const deleteDocument = (id: string) =>
  apiFetch<void>(`/api/documents/${id}`, { method: "DELETE" });

export const getDocument = (id: string) =>
  apiFetch<DocumentMeta>(`/api/documents/${id}`);

export const adaptDocument = (id: string) =>
  apiFetch<AdaptResponse>(`/api/documents/${id}/adapt`, {
    method: "POST",
    body: JSON.stringify({
      formats: ["simplified_text", "tts_audio"],
    }),
  });

export const getAdaptations = (id: string) =>
  apiFetch<AdaptResponse>(`/api/documents/${id}/adaptations`);

export function mediaUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  return `${BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export type MediaKind = "document_file" | "question_audio";
export type MediaTokenOut = { token: string; expires_in: number; url: string };

export const requestMediaToken = (kind: MediaKind, id: string) =>
  apiFetch<MediaTokenOut>("/api/media/token", {
    method: "POST",
    body: JSON.stringify({ kind, id }),
  });

export function mediaCapabilityUrl(cap: MediaTokenOut): string {
  return mediaUrl(cap.url);
}

export async function fetchProtectedMediaBlobUrl(kind: MediaKind, id: string): Promise<string> {
  const cap = await requestMediaToken(kind, id);
  const res = await fetch(`${BASE}${cap.url}`, { headers: authHeaders() });
  if (!res.ok) {
    const err: Error & { status?: number } = new Error(
      "That file link has expired. Please try again."
    );
    err.status = res.status;
    throw err;
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export type AskResponse = {
  document_id: string;
  answer: string;
  used_llm: boolean;
  sources: { chunk_index: number; snippet: string }[];
};

export const askDocument = (id: string, question: string) =>
  apiFetch<AskResponse>(`/api/documents/${id}/ask`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });

export type Sprint = {
  id: string;
  index: number;
  description: string;
  minutes: number;
  done: boolean;
};
export type Task = {
  id: string;
  title: string;
  due_date: string | null;
  notes: string | null;
  status: "open" | "done";
  created_at: string;
  sprints: Sprint[];
};

export const createTask = (title: string, due_date: string | null, notes: string | null) =>
  apiFetch<Task>("/api/tasks", {
    method: "POST",
    body: JSON.stringify({ title, due_date, notes }),
  });

export const listTasks = () => apiFetch<{ items: Task[] }>("/api/tasks");

export const toggleSprint = (taskId: string, sprintId: string) =>
  apiFetch<Task>(`/api/tasks/${taskId}/sprints/${sprintId}/toggle`, {
    method: "POST",
  });

export const deleteTask = (taskId: string) =>
  apiFetch<void>(`/api/tasks/${taskId}`, { method: "DELETE" });

export type VivaStart = {
  session_id: string;
  document_id: string;
  question: string;
  turn_count: number;
};
export type VivaAnswerOut = {
  feedback: string;
  score: number;
  next_question: string | null;
  done: boolean;
  turn_count: number;
};
export type VivaTranscript = {
  session_id: string;
  document_id: string;
  done: boolean;
  turns: {
    index: number;
    question: string;
    answer: string | null;
    feedback: string | null;
    score: number | null;
  }[];
};

export const startViva = (docId: string) =>
  apiFetch<VivaStart>(`/api/documents/${docId}/viva/start`, { method: "POST" });

export const getVivaTranscript = (sessionId: string) =>
  apiFetch<VivaTranscript>(`/api/viva/${sessionId}`);

export const answerViva = (sessionId: string, answer: string) =>
  apiFetch<VivaAnswerOut>(`/api/viva/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });

export type Checkin = {
  id: string;
  mood: number;
  note: string | null;
  suggestion: string;
  created_at: string;
};

export const createCheckin = (mood: number, note: string | null) =>
  apiFetch<Checkin>("/api/checkins", {
    method: "POST",
    body: JSON.stringify({ mood, note }),
  });

export const listCheckins = () => apiFetch<{ items: Checkin[] }>("/api/checkins");

export type RecommendOut = { format: string; reason: string };

export const getRecommendation = (docId: string) =>
  apiFetch<RecommendOut>(`/api/documents/${docId}/recommend`);

export type SttOut = { text: string; engine: string };

export const transcribeAudio = (blob: Blob) => {
  const ext = blob.type.includes("wav") ? "wav" : "webm";
  const fd = new FormData();
  fd.append("file", new File([blob], `speech.${ext}`, { type: blob.type }));
  return apiFetch<SttOut>("/api/stt", { method: "POST", body: fd });
};

export type ScoresOut = {
  scores: Record<string, number>;
  labels: Record<string, string>;
  profile_lines: string[];
  recent_events: { id: string; event: string; concept: string | null; document_id: string | null; created_at: string }[];
};

export const getPreferences = () => apiFetch<ScoresOut>("/api/preferences");

export const putPreferences = (scores: Record<string, number>) =>
  apiFetch<ScoresOut>("/api/preferences", {
    method: "PUT",
    body: JSON.stringify({ scores }),
  });

export const postInteraction = (
  event: string,
  opts?: { document_id?: string; concept?: string; metadata?: Record<string, unknown> }
) =>
  apiFetch<ScoresOut>("/api/interactions", {
    method: "POST",
    body: JSON.stringify({ event, ...opts }),
  });

export type ReaderCard = {
  index: number;
  title: string;
  simple: string;
  technical: string;
  example: string | null;
  has_visual: boolean;
  concept: string | null;
};

export type ReaderOut = {
  document_id: string;
  filename: string;
  cards: ReaderCard[];
  presentation: {
    start_level: number;
    show_example_first: boolean;
    suggest_concept_map: boolean;
    suggest_quiz_after_cards: number;
    prefer_audio: boolean;
    hints_explanation: string[];
  };
};

export const getReader = (id: string) =>
  apiFetch<ReaderOut>(`/api/documents/${id}/reader`);

export type ExplainOut = { level: number; text: string; engine: string };

export const postExplain = (
  text: string,
  level: number,
  context?: string,
  transform?: "analogy" | "bullets" | "summary" | "translate",
  targetLang = "Hindi"
) =>
  apiFetch<ExplainOut>("/api/documents/explain", {
    method: "POST",
    body: JSON.stringify({ text, level, context, transform, target_lang: targetLang }),
  });

export type QuizItem = { id: string; question: string; options: string[]; answer_index: number; concept: string | null };

export const getQuiz = (id: string, count = 3) =>
  apiFetch<{ items: QuizItem[] }>(`/api/documents/${id}/quiz`, {
    method: "POST",
    body: JSON.stringify({ count }),
  });

export type CommunicationResult =
  | string
  | { situation: string; explanation: string; request: string; deadline: string }
  | { opening: string; key_points: string[]; conclusion: string; speaker_notes: string[] };

export const postCommunication = (body: {
  mode: "email" | "structure" | "presentation";
  topic?: string;
  raw?: string;
  recipient?: string;
  deadline?: string;
}) =>
  apiFetch<{ mode: string; engine: string; result: CommunicationResult }>(
    "/api/communication",
    { method: "POST", body: JSON.stringify(body) }
  );

export const postPlan = (items: string[]) =>
  apiFetch<{ high: string[]; medium: string[]; low: string[] }>("/api/wellbeing/plan", {
    method: "POST",
    body: JSON.stringify({ items }),
  });

export type AnalyticsOut = {
  documents_count: number;
  adaptive_changes_total: number;
  adaptive_changes_last_24h: number;
  interactions_total: number;
  quiz_correct: number;
  quiz_incorrect: number;
  top_interactions: [string, number][];
};

export const getAnalytics = () => apiFetch<AnalyticsOut>("/api/analytics");

export type MemoryOut = {
  struggled_concepts: { concept: string; misses: number }[];
  suggestions: string[];
};

export const getMemory = () => apiFetch<MemoryOut>("/api/preferences/memory");

export const deleteHistory = () =>
  apiFetch<{ deleted_events: number; scores_reset: boolean }>("/api/interactions", {
    method: "DELETE",
  });

export async function downloadExport(): Promise<void> {
  const res = await fetch(`${BASE}/api/me/export`, { headers: authHeaders() });
  if (!res.ok) {
    const err: Error & { status?: number } = new Error(res.statusText || "Export failed");
    err.status = res.status;
    throw err;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "neurolearn-export.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export const deleteAccount = () =>
  apiFetch<{ detail: string }>("/api/me", { method: "DELETE" });

export async function uploadImageOcr(file: File): Promise<DocumentMeta> {
  const fd = new FormData();
  fd.append("file", file);
  return apiFetch<DocumentMeta>("/api/documents/image", { method: "POST", body: fd });
}
