"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  FileText,
  LoaderCircle,
  Play,
  RefreshCw,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { apiFetch, AnalyzeResponse, RunRecord } from "@/lib/api";
import { RunTabs } from "@/components/run-tabs";
import { StatusBadge } from "@/components/status-badge";

export function RunWorkspace() {
  const runId = decodeURIComponent(useParams<{ runId: string }>().runId);
  const [run, setRun] = useState<RunRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const loadRun = useCallback(async () => {
    setLoading(true);
    try {
      setRun(await apiFetch<RunRecord>(`/api/runs/${runId}`));
      setError("");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Run could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void loadRun();
  }, [loadRun]);

  async function analyze() {
    setAnalyzing(true);
    setError("");
    try {
      await apiFetch<AnalyzeResponse>(`/api/analyze/${runId}`, { method: "POST" });
      await loadRun();
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  if (loading && !run) return <Loading />;
  if (!run) return <ErrorPanel message={error || "Run was not found."} />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <p className="text-xs font-bold uppercase text-teal-700">{run.systemName}</p>
            <StatusBadge status={analyzing ? "processing" : run.status} />
          </div>
          <h1 className="text-2xl font-bold text-ink sm:text-3xl">{run.projectName}</h1>
          <p className="mt-2 break-all font-mono text-xs text-slate-500">{run.runId}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void loadRun()}
            className="grid size-11 place-items-center rounded-md border border-line bg-white text-slate-600 hover:bg-slate-50"
            title="Refresh run"
          >
            <RefreshCw size={17} className={loading ? "animate-spin" : ""} />
          </button>
          <button
            type="button"
            onClick={() => void analyze()}
            disabled={analyzing}
            className="flex h-11 items-center gap-2 rounded-md bg-ink px-4 text-sm font-bold text-white hover:bg-slate-700 disabled:bg-slate-400"
          >
            {analyzing ? <LoaderCircle size={17} className="animate-spin" /> : <Play size={17} />}
            {run.status === "completed" ? "Run analysis again" : "Start analysis"}
          </button>
        </div>
      </div>

      <RunTabs runId={runId} />

      {error && <ErrorPanel message={error} />}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Status" value={run.status} />
        <Metric label="Smells processed" value={run.totalProcessed ?? 0} />
        <Metric label="Recommendations" value={run.recommendationsGenerated ?? 0} />
        <Metric label="Files stored" value={Object.keys(run.uploadedFiles?.files ?? {}).length} />
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
          <h2 className="text-base font-bold text-ink">Run metadata</h2>
          <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
            <Info label="System" value={run.systemName} />
            <Info label="Created" value={formatDate(run.createdAt)} />
            <Info label="Version" value={run.version} mono />
            <Info label="Target smells" value={run.selectedSmells.join(", ")} />
          </dl>
          {run.error && (
            <div className="mt-5 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <CircleAlert size={17} className="shrink-0" />
              {run.error}
            </div>
          )}
        </section>

        <aside className="rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
          <h2 className="text-base font-bold text-ink">Uploaded files</h2>
          <div className="mt-4 space-y-4">
            {Object.values(run.uploadedFiles?.files ?? {}).map((file) => (
              <div key={file.storedPath} className="flex gap-2 text-xs">
                <FileText size={16} className="mt-0.5 shrink-0 text-teal-600" />
                <div className="min-w-0">
                  <p className="font-bold text-ink">{file.originalName}</p>
                  <p className="mt-1 break-all font-mono text-slate-500">{file.storedPath}</p>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>

      {run.status === "completed" && (
        <section className="grid gap-3 sm:grid-cols-2">
          <ActionLink href={`/runs/${runId}/recommendations`} label="View ranked recommendations" />
          <ActionLink href={`/runs/${runId}/stats`} label="View analysis statistics" />
        </section>
      )}
    </div>
  );
}

function Loading() {
  return <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-slate-500"><LoaderCircle size={18} className="animate-spin" />Loading run</div>;
}

function ErrorPanel({ message }: { message: string }) {
  return <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700"><CircleAlert size={18} className="shrink-0" />{message}</div>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-lg border border-line bg-white p-4 shadow-panel"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-bold capitalize text-ink">{value}</p></div>;
}

function Info({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return <div className="min-w-0"><dt className="text-xs text-slate-500">{label}</dt><dd className={`mt-1 break-all font-semibold text-ink ${mono ? "font-mono text-xs" : ""}`}>{value}</dd></div>;
}

function ActionLink({ href, label }: { href: string; label: string }) {
  return <Link href={href} className="flex items-center justify-between rounded-lg border border-line bg-white p-4 text-sm font-bold text-ink shadow-panel hover:border-teal-500 hover:text-teal-700"><span className="flex items-center gap-2"><CheckCircle2 size={17} className="text-teal-600" />{label}</span><ArrowRight size={17} /></Link>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
