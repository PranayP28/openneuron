"use client";

import { useRef, useState } from "react";
import type { UploadedDocument } from "@/app/lib/api";
import { FileIcon, Spinner, UploadIcon } from "./icons";

const ACCEPT = ".pdf,.txt";
const CATEGORY_LABELS: Record<string, string> = {
  rental: "Rental",
  employment: "Employment",
  legal_notice: "Legal notice",
  service_agreement: "Service agreement",
  other_legal: "Legal (other)",
  non_legal: "Not a legal document",
};

interface Props {
  document: UploadedDocument | null;
  uploading: boolean;
  onFile: (file: File) => void;
}

export function UploadPanel({ document, uploading, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pick = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFile(file);
  };

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files);
        }}
        disabled={uploading}
        className={`flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors disabled:cursor-wait ${
          dragging ? "border-accent bg-accent/5" : "border-border hover:border-accent/60 hover:bg-surface"
        }`}
      >
        {uploading ? <Spinner className="h-6 w-6 text-accent" /> : <UploadIcon width={26} height={26} className="text-accent" />}
        <span className="text-sm font-medium">{uploading ? "Analyzing document…" : "Drop a PDF or TXT here"}</span>
        <span className="text-xs text-muted">{uploading ? "Extracting, indexing and classifying locally" : "or click to browse · max 20 MB"}</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => {
          pick(e.target.files);
          e.target.value = "";
        }}
      />

      {document && (
        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-start gap-3">
            <FileIcon className="mt-0.5 shrink-0 text-muted" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium" title={document.filename}>{document.filename}</p>
              <p className="text-xs text-muted">
                {document.num_chars.toLocaleString()} chars · {document.num_chunks} chunks
              </p>
            </div>
          </div>
          <span
            className={`mt-3 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
              document.is_legal
                ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                : "bg-amber-500/10 text-amber-700 dark:text-amber-400"
            }`}
          >
            {CATEGORY_LABELS[document.category] ?? document.category}
          </span>
        </div>
      )}
    </div>
  );
}
