"use client";

import Link from "next/link";
import {
  ArrowRight,
  CircleAlert,
  Filter,
  LoaderCircle,
  Search,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, Recommendation } from "@/lib/api";
import { RunTabs } from "@/components/run-tabs";

const PAGE_SIZE = 25;

export function RecommendationsList() {
  const runId = decodeURIComponent(useParams<{ runId: string }>().runId);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [rankLevel, setRankLevel] = useState("All");
  const [smellType, setSmellType] = useState("All");
  const [page, setPage] = useState(1);

  useEffect(() => {
    apiFetch<{ recommendations: Recommendation[] }>(`/api/recommendations/${runId}`)
      .then((result) => setRecommendations(result.recommendations))
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Recommendations could not be loaded."))
      .finally(() => setLoading(false));
  }, [runId]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return recommendations.filter((item) => {
      const matchesSearch = !query || [
        item.smellId,
        item.recommendation,
        item.predictedStrategy,
        ...item.affectedElements,
      ].some((value) => value.toLowerCase().includes(query));
      return matchesSearch
        && (rankLevel === "All" || item.rankLevel === rankLevel)
        && (smellType === "All" || item.smellType === smellType);
    });
  }, [recommendations, search, rankLevel, smellType]);

  useEffect(() => setPage(1), [search, rankLevel, smellType]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const system = recommendations[0]?.system ?? "Analysis";

  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase text-teal-700">{system}</p>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">Ranked recommendations</h1>
        <p className="mt-2 text-sm text-slate-500">{recommendations.length} recommendations</p>
      </div>
      <RunTabs runId={runId} />

      <section className="rounded-lg border border-line bg-white p-4 shadow-panel">
        <div className="grid gap-3 lg:grid-cols-[minmax(240px,1fr)_200px_200px]">
          <label className="relative block">
            <Search size={17} className="absolute left-3 top-3 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search components, strategy, or smell ID"
              className="h-11 w-full rounded-md border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            />
          </label>
          <FilterSelect label="Priority" value={rankLevel} onChange={setRankLevel} options={["All", "Critical", "High", "Medium", "Low"]} />
          <FilterSelect label="Smell type" value={smellType} onChange={setSmellType} options={["All", "godComponent", "unstableDep", "cyclicDep"]} />
        </div>
      </section>

      {error ? (
        <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700"><CircleAlert size={18} />{error}</div>
      ) : loading ? (
        <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-slate-500"><LoaderCircle size={18} className="animate-spin" />Loading recommendations</div>
      ) : visible.length === 0 ? (
        <div className="rounded-lg border border-line bg-white p-10 text-center text-sm text-slate-500 shadow-panel">No recommendations match these filters.</div>
      ) : (
        <section className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
          <div className="divide-y divide-line">
            {visible.map((item) => (
              <article key={item.smellId} className="grid gap-4 p-5 hover:bg-slate-50 sm:p-6 lg:grid-cols-[70px_minmax(0,1fr)_180px_auto] lg:items-center">
                <div>
                  <p className="text-xs text-slate-500">Rank</p>
                  <p className="mt-1 text-2xl font-bold text-ink">#{item.rankPosition}</p>
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-sm font-bold text-ink">{item.recommendation}</h2>
                    <RankBadge level={item.rankLevel} />
                    <span className="rounded bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-600">{item.smellType}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm leading-5 text-slate-600">{item.reason}</p>
                  <p className="mt-2 truncate font-mono text-xs text-slate-500">{item.smellId} · {item.affectedElements.join(", ")}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Ranking score</p>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded bg-slate-200">
                      <div className="h-full bg-teal-600" style={{ width: `${item.finalRankingScore * 100}%` }} />
                    </div>
                    <span className="text-sm font-bold text-ink">{item.finalRankingScore.toFixed(3)}</span>
                  </div>
                </div>
                <Link
                  href={`/runs/${runId}/recommendations/${item.smellId}`}
                  className="grid size-10 place-items-center rounded-md border border-line text-slate-600 hover:border-teal-500 hover:text-teal-700"
                  title={`Open ${item.smellId}`}
                >
                  <ArrowRight size={17} />
                </Link>
              </article>
            ))}
          </div>
          <div className="flex flex-col gap-3 border-t border-line px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-500">Showing {(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}</p>
            <div className="flex gap-2">
              <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1} className="h-9 rounded-md border border-line px-3 text-sm font-bold text-slate-600 disabled:text-slate-300">Previous</button>
              <span className="grid h-9 min-w-20 place-items-center text-xs text-slate-500">{page} / {pageCount}</span>
              <button type="button" onClick={() => setPage((current) => Math.min(pageCount, current + 1))} disabled={page === pageCount} className="h-9 rounded-md border border-line px-3 text-sm font-bold text-slate-600 disabled:text-slate-300">Next</button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <label className="relative block">
      <Filter size={15} className="pointer-events-none absolute left-3 top-3.5 text-slate-400" />
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="h-11 w-full rounded-md border border-slate-300 bg-white pl-9 pr-3 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100">
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}

export function RankBadge({ level }: { level: string }) {
  const style = level === "Critical" ? "bg-red-100 text-red-700" : level === "High" ? "bg-amber-100 text-amber-800" : level === "Medium" ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600";
  return <span className={`rounded px-2 py-1 text-[11px] font-bold ${style}`}>{level}</span>;
}
