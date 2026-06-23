"use client";

import Link from "next/link";
import { BarChart3, LayoutDashboard, ListOrdered } from "lucide-react";
import { usePathname } from "next/navigation";

export function RunTabs({ runId }: { runId: string }) {
  const pathname = usePathname();
  const tabs = [
    { href: `/runs/${runId}`, label: "Overview", icon: LayoutDashboard },
    { href: `/runs/${runId}/recommendations`, label: "Recommendations", icon: ListOrdered },
    { href: `/runs/${runId}/stats`, label: "Statistics", icon: BarChart3 },
  ];

  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-line" aria-label="Run views">
      {tabs.map(({ href, label, icon: Icon }) => {
        const active =
          href === `/runs/${runId}`
            ? pathname === href
            : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`flex h-11 shrink-0 items-center gap-2 border-b-2 px-3 text-sm font-bold ${
              active
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-ink"
            }`}
          >
            <Icon size={16} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
