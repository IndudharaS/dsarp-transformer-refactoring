"use client";

import Link from "next/link";
import {
  ArrowLeft,
  Check,
  CircleAlert,
  FlaskConical,
  Layers3,
  LoaderCircle,
  Target,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, Recommendation } from "@/lib/api";
import { RankBadge } from "@/components/recommendations-list";
import { RunTabs } from "@/components/run-tabs";

export function RecommendationDetail() {
  const params = useParams<{ runId: string; smellId: string }>();
  const runId = decodeURIComponent(params.runId);
  const smellId = decodeURIComponent(params.smellId);
  const [item, setItem] = useState<Recommendation | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Recommendation>(`/api/recommendations/${runId}/${smellId}`)
      .then(setItem)
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Recommendation could not be loaded."));
  }, [runId, smellId]);

  if (error) return <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700"><CircleAlert size={18} />{error}</div>;
  if (!item) return <div className="flex min-h-64 items-center justify-center gap-2 text-sm text-slate-500"><LoaderCircle size={18} className="animate-spin" />Loading recommendation</div>;

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/runs/${runId}/recommendations`} className="mb-4 inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-teal-700"><ArrowLeft size={16} />All recommendations</Link>
        <div className="flex flex-wrap items-center gap-2">
          <RankBadge level={item.rankLevel} />
          <span className="rounded bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-600">{item.smellType}</span>
          <span className="font-mono text-xs text-slate-500">{item.smellId}</span>
        </div>
        <h1 className="mt-3 text-2xl font-bold text-ink sm:text-3xl">{item.recommendation}</h1>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">{item.reason}</p>
      </div>
      <RunTabs runId={runId} />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Score label="Final score" value={item.finalRankingScore} />
        <Score label="Priority score" value={item.smellPriorityScore} />
        <Score label="Quality score" value={item.recommendationQualityScore} />
        <Score label="Classifier confidence" value={item.classifierConfidence} />
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <section className="rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
            <div className="flex items-center gap-2"><Target size={18} className="text-teal-600" /><h2 className="text-base font-bold text-ink">Refactoring steps</h2></div>
            <ol className="mt-5 space-y-4">
              {item.steps.map((step, index) => (
                <li key={step} className="flex gap-3 text-sm leading-6 text-slate-700">
                  <span className="grid size-6 shrink-0 place-items-center rounded bg-ink text-xs font-bold text-white">{index + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </section>
          <section className="grid gap-4 sm:grid-cols-2">
            <TextPanel icon={Layers3} title="Expected impact" text={item.expectedImpact} />
            <TextPanel icon={FlaskConical} title="Testing advice" text={item.testingAdvice} />
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
            <h2 className="text-base font-bold text-ink">Affected components</h2>
            <div className="mt-4 space-y-2">
              {item.targetComponents.map((component) => (
                <div key={component} className="flex gap-2 rounded-md bg-slate-50 p-2 font-mono text-xs text-slate-700"><Check size={14} className="mt-0.5 shrink-0 text-teal-600" /><span className="break-all">{component}</span></div>
              ))}
            </div>
          </section>
          <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
            <h2 className="text-base font-bold text-ink">Model details</h2>
            <dl className="mt-4 space-y-3 text-xs">
              <Detail label="Predicted strategy" value={item.predictedStrategy} />
              <Detail label="Classifier" value={item.classifierModel} />
              <Detail label="Recommendation model" value={item.modelUsed} />
              <Detail label="Prompt version" value={item.promptVersion} />
              <Detail label="Fallback used" value={item.usedFallback ? "Yes" : "No"} />
              <Detail label="Risk" value={item.risk} />
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return <div className="rounded-lg border border-line bg-white p-4 shadow-panel"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-bold text-ink">{value.toFixed(3)}</p><div className="mt-3 h-2 overflow-hidden rounded bg-slate-200"><div className="h-full bg-teal-600" style={{ width: `${Math.min(100, value * 100)}%` }} /></div></div>;
}

function TextPanel({ icon: Icon, title, text }: { icon: typeof Layers3; title: string; text: string }) {
  return <section className="rounded-lg border border-line bg-white p-5 shadow-panel"><div className="flex items-center gap-2"><Icon size={18} className="text-teal-600" /><h2 className="text-sm font-bold text-ink">{title}</h2></div><p className="mt-3 text-sm leading-6 text-slate-600">{text}</p></section>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4"><dt className="text-slate-500">{label}</dt><dd className="text-right font-bold text-ink">{value}</dd></div>;
}
