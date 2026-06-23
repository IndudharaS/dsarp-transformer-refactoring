"use client";

import Link from "next/link";
import {
  ArrowRight,
  CircleAlert,
  Layers3,
  Lightbulb,
  LoaderCircle,
  ShieldAlert,
  Target,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, StatsResponse } from "@/lib/api";
import { RunTabs } from "@/components/run-tabs";
import { RankBadge } from "@/components/recommendations-list";

export function StatsDashboard() {
  const runId = decodeURIComponent(useParams<{ runId: string }>().runId);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<StatsResponse>(`/api/stats/${runId}`)
      .then(setStats)
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Statistics could not be loaded."));
  }, [runId]);

  if (error) return <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700"><CircleAlert size={18} />{error}</div>;
  if (!stats) return <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-slate-500"><LoaderCircle size={18} className="animate-spin" />Loading statistics</div>;

  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase text-teal-700">{stats.system}</p>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">Analysis statistics</h1>
      </div>
      <RunTabs runId={runId} />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Summary icon={Layers3} label="Smells processed" value={stats.totalSmellsProcessed} />
        <Summary icon={Lightbulb} label="Recommendations" value={stats.recommendationsGenerated} accent />
        <Summary icon={Target} label="Strategy classes" value={Object.keys(stats.predictedStrategies).length} />
        <Summary icon={ShieldAlert} label="High risk items" value={stats.riskDistribution.High ?? 0} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Distribution title="Smells by type" values={stats.smellsByType} total={stats.totalSmellsProcessed} />
        <Distribution title="Priority distribution" values={stats.priorityDistribution} total={stats.recommendationsGenerated} />
        <Distribution title="Predicted strategies" values={stats.predictedStrategies} total={stats.recommendationsGenerated} />
        <Distribution title="Risk distribution" values={stats.riskDistribution} total={stats.recommendationsGenerated} />
      </section>

      <section className="rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
        <h2 className="text-base font-bold text-ink">Average severity by smell type</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {Object.entries(stats.averageSeverityBySmellType).map(([label, value]) => (
            <div key={label} className="rounded-md border border-line p-4">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-1 text-2xl font-bold text-ink">{value.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="border-b border-line px-5 py-4 sm:px-6"><h2 className="text-base font-bold text-ink">Top recommendations</h2></div>
        <div className="divide-y divide-line">
          {stats.topRecommendations.map((item) => (
            <div key={item.smellId} className="grid gap-3 px-5 py-4 sm:px-6 lg:grid-cols-[60px_minmax(0,1fr)_auto] lg:items-center">
              <p className="text-xl font-bold text-ink">#{item.rankPosition}</p>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2"><p className="text-sm font-bold text-ink">{item.recommendation}</p><RankBadge level={item.rankLevel} /></div>
                <p className="mt-1 truncate font-mono text-xs text-slate-500">{item.smellId} · {item.predictedStrategy}</p>
              </div>
              <Link href={`/runs/${runId}/recommendations/${item.smellId}`} className="flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-bold text-slate-600 hover:border-teal-500 hover:text-teal-700">Open <ArrowRight size={15} /></Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Summary({ icon: Icon, label, value, accent = false }: { icon: typeof Layers3; label: string; value: number; accent?: boolean }) {
  return <div className="flex items-center gap-4 rounded-lg border border-line bg-white p-4 shadow-panel"><span className={`grid size-10 shrink-0 place-items-center rounded-md ${accent ? "bg-teal-100 text-teal-700" : "bg-slate-100 text-slate-600"}`}><Icon size={19} /></span><div><p className="text-xs text-slate-500">{label}</p><p className="text-xl font-bold text-ink">{value}</p></div></div>;
}

function Distribution({ title, values, total }: { title: string; values: Record<string, number>; total: number }) {
  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
      <h2 className="text-base font-bold text-ink">{title}</h2>
      <div className="mt-5 space-y-4">
        {Object.entries(values).sort((a, b) => b[1] - a[1]).map(([label, value]) => {
          const percentage = total ? (value / total) * 100 : 0;
          return <div key={label}><div className="mb-2 flex justify-between gap-4 text-xs"><span className="font-semibold text-slate-700">{label}</span><span className="text-slate-500">{value} · {percentage.toFixed(1)}%</span></div><div className="h-2 overflow-hidden rounded bg-slate-200"><div className="h-full bg-teal-600" style={{ width: `${percentage}%` }} /></div></div>;
        })}
      </div>
    </section>
  );
}
