"use client";

import Link from "next/link";
import {
  ArrowRight,
  CircleAlert,
  Database,
  FileCheck2,
  LoaderCircle,
  Play,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch, AnalyzeResponse, RunRecord } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";

export function RunsList() {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState<string | null>(null);

  const loadRuns = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<{ runs: RunRecord[] }>("/api/runs?limit=100");
      setRuns(result.runs);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Runs could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  async function analyze(runId: string) {
    setAnalyzing(runId);
    setError("");
    try {
      await apiFetch<AnalyzeResponse>(`/api/analyze/${runId}`, { method: "POST" });
      await loadRuns();
    } catch (analysisError) {
      setError(
        analysisError instanceof Error ? analysisError.message : "Analysis failed.",
      );
    } finally {
      setAnalyzing(null);
    }
  }

  const completed = runs.filter((run) => run.status === "completed").length;

  return (
    <div className="space-y-5">
      <section className="grid gap-3 sm:grid-cols-3">
        <Summary icon={Database} label="Total runs" value={runs.length} />
        <Summary icon={FileCheck2} label="Completed" value={completed} accent />
        <Summary icon={Play} label="Ready to analyze" value={runs.filter((run) => run.status === "uploaded").length} />
      </section>

      <section className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6">
          <h2 className="text-base font-bold text-ink">Recent runs</h2>
          <button
            type="button"
            onClick={() => void loadRuns()}
            className="grid size-10 place-items-center rounded-md border border-line text-slate-600 hover:bg-slate-50"
            title="Refresh runs"
          >
            <RefreshCw size={17} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {error && (
          <div className="m-5 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <CircleAlert size={17} className="shrink-0" />
            {error}
          </div>
        )}

        {loading && runs.length === 0 ? (
          <div className="flex min-h-52 items-center justify-center gap-2 text-sm text-slate-500">
            <LoaderCircle size={18} className="animate-spin" />
            Loading runs
          </div>
        ) : runs.length === 0 ? (
          <div className="min-h-52 p-8 text-center text-sm text-slate-500">
            No analysis runs found.
          </div>
        ) : (
          <div className="divide-y divide-line">
            {runs.map((run) => {
              const isAnalyzing = analyzing === run.runId;
              return (
                <article
                  key={run.runId}
                  className="grid gap-4 px-5 py-5 hover:bg-slate-50 sm:px-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-bold text-ink">{run.projectName}</h3>
                      <StatusBadge status={isAnalyzing ? "processing" : run.status} />
                    </div>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                      <span>{run.systemName}</span>
                      <span>{formatDate(run.createdAt)}</span>
                      <span className="break-all font-mono">{run.runId}</span>
                    </div>
                    {run.status === "completed" && (
                      <div className="mt-3 flex gap-4 text-xs">
                        <span><strong className="text-ink">{run.totalProcessed ?? 0}</strong> smells</span>
                        <span><strong className="text-ink">{run.recommendationsGenerated ?? 0}</strong> recommendations</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void analyze(run.runId)}
                      disabled={isAnalyzing}
                      className="flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-bold text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
                    >
                      {isAnalyzing ? <LoaderCircle size={16} className="animate-spin" /> : <Play size={16} />}
                      {run.status === "completed" ? "Run again" : "Analyze"}
                    </button>
                    <Link
                      href={`/runs/${run.runId}`}
                      className="flex h-10 items-center gap-2 rounded-md bg-ink px-3 text-sm font-bold text-white hover:bg-slate-700"
                    >
                      Open <ArrowRight size={16} />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function Summary({
  icon: Icon,
  label,
  value,
  accent = false,
}: {
  icon: typeof Database;
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-line bg-white p-4 shadow-panel">
      <span className={`grid size-10 place-items-center rounded-md ${accent ? "bg-teal-100 text-teal-700" : "bg-slate-100 text-slate-600"}`}>
        <Icon size={19} />
      </span>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-xl font-bold text-ink">{value}</p>
      </div>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
