import { CheckCircle2, CircleAlert, Clock3, LoaderCircle } from "lucide-react";

const styles: Record<string, string> = {
  completed: "bg-teal-100 text-teal-700",
  uploaded: "bg-blue-100 text-blue-700",
  validating: "bg-amber-100 text-amber-700",
  processing: "bg-amber-100 text-amber-700",
  failed: "bg-red-100 text-red-700",
};

export function StatusBadge({ status }: { status: string }) {
  const working = status === "validating" || status === "processing";
  const Icon = status === "completed"
    ? CheckCircle2
    : status === "failed"
      ? CircleAlert
      : working
        ? LoaderCircle
        : Clock3;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold capitalize ${
        styles[status] ?? "bg-slate-100 text-slate-600"
      }`}
    >
      <Icon size={13} className={working ? "animate-spin" : ""} />
      {status}
    </span>
  );
}
