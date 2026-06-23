"use client";

import { Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export function ApiStatus() {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    apiFetch<{ status: string; database: boolean }>("/api/health")
      .then((result) => setHealthy(result.status === "ok" && result.database))
      .catch(() => setHealthy(false));
  }, []);

  return (
    <span
      className={`hidden h-8 items-center gap-2 rounded-md border px-2 text-xs font-bold lg:flex ${
        healthy === true
          ? "border-teal-100 bg-teal-50 text-teal-700"
          : healthy === false
            ? "border-red-200 bg-red-50 text-red-700"
            : "border-line bg-slate-50 text-slate-500"
      }`}
      title={healthy ? "API and MongoDB connected" : "API connection status"}
    >
      <Activity size={14} />
      {healthy === null ? "Checking" : healthy ? "Connected" : "Offline"}
    </span>
  );
}
