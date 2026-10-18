"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SectionCard } from "@/app/components/SectionCard";
import { UploadPanel } from "@/app/components/UploadPanel";
import { AlertIcon, SendIcon, ShieldIcon, StopIcon, XIcon } from "@/app/components/icons";
import { checkHealth, streamChat, uploadDocument, type Section, type UploadedDocument } from "@/app/lib/api";

const SECTIONS = [
  { category: "clause", title: "Clauses" },
  { category: "risk", title: "Risks" },
  { category: "obligation", title: "Obligations" },
  { category: "deadline", title: "Deadlines" },
] as const;

const SUGGESTIONS = [
  "Summarize the key terms",
  "What are my payment obligations?",
  "How can this agreement be terminated?",
  "Are there any unusual or one-sided terms?",
];

type Message =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "info"; text: string }
  | {
      id: string;
      role: "analysis";
      stage: "retrieving" | "analyzing" | "done";
      sections: Record<string, Section>;
      response?: string;
      elapsedMs?: number;
      error?: string;
    };

const newId = () => Math.random().toString(36).slice(2);

export default function ChatPage() {
  const [doc, setDoc] = useState<UploadedDocument | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backend, setBackend] = useState<{ online: boolean; model?: string } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    checkHealth(controller.signal).then((h) => {
      if (!controller.signal.aborted) setBackend(h ? { online: true, model: h.model } : { online: false });
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const updateAnalysis = useCallback((id: string, patch: (m: Extract<Message, { role: "analysis" }>) => Partial<Message>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id && m.role === "analysis" ? ({ ...m, ...patch(m) } as Message) : m)),
    );
  }, []);

  const handleFile = async (file: File) => {
    abortRef.current?.abort();
    setError(null);
    setUploading(true);
    try {
      const uploaded = await uploadDocument(file);
      setDoc(uploaded);
      setBackend((b) => (b?.online ? b : { online: true, model: b?.model }));
      setMessages([
        {
          id: newId(),
          role: "info",
          text: uploaded.is_legal
            ? `“${uploaded.filename}” is ready. Ask anything about it — clauses, risks, obligations and deadlines are analyzed in parallel.`
            : `“${uploaded.filename}” does not appear to be a legal document, so it can't be analyzed.`,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  };

  const send = async (text: string) => {
    const query = text.trim();
    if (!query || !doc || busy) return;

    const analysisId = newId();
    setMessages((prev) => [
      ...prev,
      { id: newId(), role: "user", text: query },
      { id: analysisId, role: "analysis", stage: "retrieving", sections: {} },
    ]);
    setInput("");
    setError(null);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamChat(
        doc.doc_id,
        query,
        (event) => {
          switch (event.type) {
            case "status":
              updateAnalysis(analysisId, () => ({ stage: event.stage }));
              break;
            case "section":
              updateAnalysis(analysisId, (m) => ({
                stage: "analyzing",
                sections: { ...m.sections, [event.section.category]: event.section },
              }));
              break;
            case "final":
              updateAnalysis(analysisId, () => ({ stage: "done", response: event.response, elapsedMs: event.elapsed_ms }));
              break;
            case "error":
              updateAnalysis(analysisId, () => ({ stage: "done", error: event.message }));
              break;
          }
        },
        controller.signal,
      );
    } catch (e) {
      const aborted = controller.signal.aborted;
      updateAnalysis(analysisId, () => ({
        stage: "done",
        error: aborted ? "Stopped." : e instanceof Error ? e.message : "Error connecting to backend.",
      }));
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setBusy(false);
    }
  };

  const canChat = !!doc?.is_legal && !uploading;

  return (
    <div className="flex h-dvh flex-col bg-background text-foreground">
      <header className="flex items-center gap-3 border-b border-border bg-surface/80 px-5 py-3 backdrop-blur">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white">
          <ShieldIcon />
        </span>
        <div>
          <h1 className="text-base font-semibold leading-tight">ZeroDay Legal Triage</h1>
          <p className="text-xs text-muted">Private, on-device document analysis · not legal advice</p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-muted">
          <span
            className={`h-2 w-2 rounded-full ${
              backend === null ? "bg-muted animate-pulse" : backend.online ? "bg-emerald-500" : "bg-rose-500"
            }`}
          />
          {backend === null ? "Connecting…" : backend.online ? `Local model · ${backend.model ?? ""}` : "Backend offline"}
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <aside className="shrink-0 border-b border-border p-5 md:w-80 md:border-b-0 md:border-r md:overflow-y-auto">
          <UploadPanel document={doc} uploading={uploading} onFile={handleFile} />
          <p className="mt-6 hidden text-xs leading-relaxed text-muted md:block">
            Documents never leave this machine. Every finding is checked against the source text and filtered for
            legal verdicts before it is shown.
          </p>
        </aside>

        <main className="flex min-h-0 flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
            <div className="mx-auto flex max-w-4xl flex-col gap-5">
              {messages.length === 0 && (
                <div className="mt-16 text-center">
                  <h2 className="text-lg font-semibold">Upload a legal document to begin</h2>
                  <p className="mt-1 text-sm text-muted">Leases, employment contracts, service agreements and legal notices.</p>
                </div>
              )}

              {messages.map((m) => {
                if (m.role === "user") {
                  return (
                    <div key={m.id} className="flex justify-end">
                      <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-accent px-4 py-2.5 text-sm text-white shadow-sm">
                        {m.text}
                      </div>
                    </div>
                  );
                }
                if (m.role === "info") {
                  return (
                    <div key={m.id} className="rounded-xl border border-border bg-surface px-4 py-3 text-sm text-muted">
                      {m.text}
                    </div>
                  );
                }
                const hasSections = Object.keys(m.sections).length > 0;
                const showGrid = m.stage === "analyzing" || hasSections;
                return (
                  <div key={m.id} className="space-y-3">
                    {m.stage === "retrieving" && (
                      <p className="flex items-center gap-2 text-sm text-muted">
                        <span className="h-2 w-2 animate-ping rounded-full bg-accent" /> Finding relevant passages…
                      </p>
                    )}
                    {showGrid && (
                      <div className="grid gap-3 sm:grid-cols-2">
                        {SECTIONS.map((s) => (
                          <SectionCard
                            key={s.category}
                            title={s.title}
                            category={s.category}
                            section={m.sections[s.category] ?? (m.stage === "done" ? errorSection(s) : undefined)}
                          />
                        ))}
                      </div>
                    )}
                    {!hasSections && m.stage === "done" && m.response && (
                      <div className="rounded-xl border border-border bg-surface px-4 py-3 text-sm">{m.response}</div>
                    )}
                    {m.error && (
                      <p className="flex items-center gap-2 text-sm text-rose-600 dark:text-rose-400">
                        <AlertIcon width={14} height={14} /> {m.error}
                      </p>
                    )}
                    {m.stage === "done" && m.elapsedMs !== undefined && hasSections && (
                      <p className="text-xs text-muted">Completed in {(m.elapsedMs / 1000).toFixed(1)}s</p>
                    )}
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </div>

          <footer className="border-t border-border bg-surface/60 px-4 py-4 md:px-8">
            <div className="mx-auto max-w-4xl">
              {error && (
                <div className="mb-3 flex items-start gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-700 dark:text-rose-300">
                  <AlertIcon className="mt-0.5 shrink-0" width={16} height={16} />
                  <span className="flex-1">{error}</span>
                  <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">
                    <XIcon width={16} height={16} />
                  </button>
                </div>
              )}
              {canChat && messages.length <= 1 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => send(s)}
                      disabled={busy}
                      className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted transition-colors hover:border-accent hover:text-foreground disabled:opacity-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <form
                className="flex items-end gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  send(input);
                }}
              >
                <textarea
                  value={input}
                  rows={1}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                      e.preventDefault();
                      send(input);
                    }
                  }}
                  placeholder={canChat ? "Ask a question about the document…" : "Upload a legal document first"}
                  disabled={!canChat}
                  aria-label="Question"
                  className="max-h-40 min-h-[44px] flex-1 resize-none rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/30 disabled:opacity-60"
                />
                {busy ? (
                  <button
                    type="button"
                    onClick={() => abortRef.current?.abort()}
                    className="flex h-11 items-center gap-1.5 rounded-xl border border-border bg-surface px-4 text-sm font-medium hover:bg-background"
                  >
                    <StopIcon width={16} height={16} /> Stop
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!canChat || !input.trim()}
                    className="flex h-11 items-center gap-1.5 rounded-xl bg-accent px-4 text-sm font-medium text-white shadow-sm transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Send <SendIcon width={16} height={16} />
                  </button>
                )}
              </form>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

function errorSection(s: { category: string; title: string }): Section {
  return {
    category: s.category,
    title: s.title,
    findings: ["No result."],
    evidence: [],
    grounded: false,
    status: "error",
    elapsed_ms: 0,
  };
}
