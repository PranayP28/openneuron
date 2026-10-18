import type { Section } from "@/app/lib/api";
import { AlertIcon, CheckIcon, Spinner } from "./icons";
import { Markdown } from "./Markdown";

const ACCENTS: Record<string, string> = {
  clause: "bg-sky-500",
  risk: "bg-rose-500",
  obligation: "bg-amber-500",
  deadline: "bg-violet-500",
};

const STATUS_BADGE: Record<Section["status"], { label: string; className: string }> = {
  ok: { label: "Grounded", className: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400" },
  ungrounded: { label: "Unverified", className: "bg-amber-500/10 text-amber-700 dark:text-amber-400" },
  blocked: { label: "Blocked by safety", className: "bg-rose-500/10 text-rose-700 dark:text-rose-400" },
  error: { label: "Model error", className: "bg-rose-500/10 text-rose-700 dark:text-rose-400" },
};

export function SectionCard({ title, category, section }: { title: string; category: string; section?: Section }) {
  const badge = section ? STATUS_BADGE[section.status] : null;
  return (
    <article className="flex flex-col rounded-xl border border-border bg-surface p-4 shadow-sm transition-shadow hover:shadow-md">
      <header className="mb-2 flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${ACCENTS[category] ?? "bg-muted"}`} />
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="ml-auto flex items-center gap-2 text-xs text-muted">
          {section ? (
            <>
              {badge && (
                <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${badge.className}`}>
                  {section.status === "ok" ? <CheckIcon width={12} height={12} /> : <AlertIcon width={12} height={12} />}
                  {badge.label}
                </span>
              )}
              <span className="tabular-nums">{(section.elapsed_ms / 1000).toFixed(1)}s</span>
            </>
          ) : (
            <Spinner className="text-muted" />
          )}
        </span>
      </header>

      {section ? (
        <>
          <Markdown text={section.findings[0]} />
          {section.evidence.length > 0 && (
            <details className="group mt-3 text-xs">
              <summary className="cursor-pointer select-none text-muted hover:text-foreground">
                Evidence ({section.evidence.length})
              </summary>
              <ul className="mt-2 space-y-2">
                {section.evidence.map((e, i) => (
                  <li key={i} className="rounded-md border-l-2 border-accent/60 bg-background px-3 py-2 italic text-muted">
                    “{e}”
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      ) : (
        <div className="space-y-2" aria-hidden>
          <div className="h-3 w-11/12 animate-pulse rounded bg-border" />
          <div className="h-3 w-4/5 animate-pulse rounded bg-border" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-border" />
        </div>
      )}
    </article>
  );
}
