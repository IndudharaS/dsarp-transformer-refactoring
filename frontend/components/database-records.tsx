"use client";

import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Database,
  FileText,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { API_URL, getApiError, RunRecord } from "@/lib/api";

export function DatabaseRecords() {
  const searchParams = useSearchParams();
  const highlightedRunId = searchParams.get("runId");
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [expanded, setExpanded] = useState<string | null>(highlightedRunId);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRuns = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/runs?limit=50`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error(await getApiError(response));
      const body = (await response.json()) as { runs: RunRecord[] };
      setRuns(body.runs);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Database records could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  const verifiedCount = runs.filter((run) => run.databaseVerified).length;

  return (
    <div className="space-y-5">
      <section className="grid gap-3 sm:grid-cols-3">
        <Summary label="Runs loaded" value={runs.length.toString()} icon={Database} />
        <Summary
          label="Fully verified"
          value={verifiedCount.toString()}
          icon={CheckCircle2}
          accent
        />
        <Summary
          label="Missing metadata"
          value={(runs.length - verifiedCount).toString()}
          icon={CircleAlert}
        />
      </section>

      <section className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
          <div>
            <h2 className="text-base font-bold text-ink">Recent analysis runs</h2>
            <p className="mt-1 text-xs text-slate-500">
              Latest 50 records from the online database
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadRuns()}
            disabled={loading}
            className="grid size-10 shrink-0 place-items-center rounded-md border border-line bg-white text-slate-600 hover:bg-slate-50 disabled:text-slate-300"
            title="Refresh database records"
          >
            <RefreshCw size={17} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {error ? (
          <div className="m-5 flex gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <CircleAlert size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        ) : loading && runs.length === 0 ? (
          <div className="flex min-h-48 items-center justify-center gap-2 text-sm text-slate-500">
            <LoaderCircle size={18} className="animate-spin" />
            Loading MongoDB records
          </div>
        ) : runs.length === 0 ? (
          <div className="flex min-h-48 flex-col items-center justify-center px-6 text-center">
            <Database size={26} className="text-slate-300" />
            <p className="mt-3 text-sm font-bold text-ink">No runs stored yet</p>
            <p className="mt-1 text-xs text-slate-500">
              Upload a dataset and return here to verify it.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-line">
            {runs.map((run) => {
              const isExpanded = expanded === run.runId;
              const isHighlighted = run.runId === highlightedRunId;
              return (
                <article
                  key={run.runId}
                  className={isHighlighted ? "bg-teal-50/60" : "bg-white"}
                >
                  <button
                    type="button"
                    onClick={() => setExpanded(isExpanded ? null : run.runId)}
                    className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-5 py-4 text-left hover:bg-slate-50 sm:px-6"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="truncate text-sm font-bold text-ink">
                          {run.projectName}
                        </h3>
                        <StatusBadge verified={run.databaseVerified} />
                      </div>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                        <span>{run.systemName}</span>
                        <span>{formatDate(run.createdAt)}</span>
                        <span className="font-mono">{run.runId}</span>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp size={18} className="text-slate-500" />
                    ) : (
                      <ChevronDown size={18} className="text-slate-500" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="border-t border-line bg-slate-50 px-5 py-5 sm:px-6">
                      <div className="grid gap-5 lg:grid-cols-2">
                        <div>
                          <p className="text-xs font-bold uppercase text-slate-500">
                            analysis_runs
                          </p>
                          <dl className="mt-3 grid grid-cols-[110px_minmax(0,1fr)] gap-x-3 gap-y-2 text-xs">
                            <dt className="text-slate-500">Status</dt>
                            <dd className="font-semibold text-ink">{run.status}</dd>
                            <dt className="text-slate-500">System</dt>
                            <dd className="font-semibold text-ink">{run.systemName}</dd>
                            <dt className="text-slate-500">Version</dt>
                            <dd className="break-all font-mono text-ink">{run.version}</dd>
                            <dt className="text-slate-500">Smells</dt>
                            <dd className="text-ink">{run.selectedSmells.join(", ")}</dd>
                          </dl>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase text-slate-500">
                            uploaded_files
                          </p>
                          {run.uploadedFiles ? (
                            <div className="mt-3 space-y-3">
                              {Object.entries(run.uploadedFiles.files).map(
                                ([key, file]) => (
                                  <div key={key} className="flex min-w-0 gap-2 text-xs">
                                    <FileText size={15} className="mt-0.5 shrink-0 text-teal-600" />
                                    <div className="min-w-0">
                                      <p className="font-semibold text-ink">{file.originalName}</p>
                                      <p className="mt-0.5 break-all font-mono text-slate-500">
                                        {file.storedPath}
                                      </p>
                                    </div>
                                  </div>
                                ),
                              )}
                            </div>
                          ) : (
                            <p className="mt-3 text-xs text-red-700">
                              No matching uploaded_files document was found.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function StatusBadge({ verified }: { verified: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold ${
        verified ? "bg-teal-100 text-teal-700" : "bg-red-100 text-red-700"
      }`}
    >
      {verified ? <CheckCircle2 size={13} /> : <CircleAlert size={13} />}
      {verified ? "Stored in both collections" : "Metadata missing"}
    </span>
  );
}

function Summary({
  label,
  value,
  icon: Icon,
  accent = false,
}: {
  label: string;
  value: string;
  icon: typeof Database;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-line bg-white p-4 shadow-panel">
      <span
        className={`grid size-10 shrink-0 place-items-center rounded-md ${
          accent ? "bg-teal-100 text-teal-700" : "bg-slate-100 text-slate-600"
        }`}
      >
        <Icon size={19} />
      </span>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="mt-0.5 text-xl font-bold text-ink">{value}</p>
      </div>
    </div>
  );
}
