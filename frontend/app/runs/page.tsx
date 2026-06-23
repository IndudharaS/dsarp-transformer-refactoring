import { RunsList } from "@/components/runs-list";

export default function RunsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase text-teal-700">Analysis workspace</p>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">Analysis runs</h1>
      </div>
      <RunsList />
    </div>
  );
}
