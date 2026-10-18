export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export type SectionStatus = "ok" | "ungrounded" | "blocked" | "error";

export interface Section {
  category: string;
  title: string;
  findings: string[];
  evidence: string[];
  grounded: boolean;
  status: SectionStatus;
  elapsed_ms: number;
}

export interface UploadedDocument {
  doc_id: string;
  filename: string;
  category: string;
  is_legal: boolean;
  num_chunks: number;
  num_chars: number;
}

export type StreamEvent =
  | { type: "status"; stage: "retrieving" | "analyzing" }
  | { type: "section"; section: Section }
  | { type: "final"; response: string; elapsed_ms: number }
  | { type: "error"; message: string };

async function errorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
  } catch {
    // fall through to the generic message
  }
  return `Request failed (${res.status})`;
}

export async function checkHealth(signal?: AbortSignal): Promise<{ model: string } | null> {
  try {
    const res = await fetch(`${API_URL}/health`, { signal, cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export async function uploadDocument(file: File, signal?: AbortSignal): Promise<UploadedDocument> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_URL}/upload`, { method: "POST", body, signal });
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function streamChat(
  docId: string,
  query: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const body = new FormData();
  body.append("doc_id", docId);
  body.append("query", query);
  const res = await fetch(`${API_URL}/chat/stream`, { method: "POST", body, signal });
  if (!res.ok || !res.body) throw new Error(await errorMessage(res));

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (value) buffer += decoder.decode(value, { stream: !done });
    let newline: number;
    while ((newline = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) onEvent(JSON.parse(line) as StreamEvent);
    }
    if (done) break;
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as StreamEvent);
}
