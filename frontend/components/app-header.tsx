"use client";

import Link from "next/link";
import { Database, ListTree, UploadCloud } from "lucide-react";
import { usePathname } from "next/navigation";
import { ApiStatus } from "@/components/api-status";

const navItems = [
  { href: "/", label: "Upload", icon: UploadCloud },
  { href: "/runs", label: "Runs", icon: ListTree },
  { href: "/database", label: "Database records", icon: Database },
];

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-md bg-ink text-sm font-bold text-white">
            DS
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-bold text-ink">DSARP</span>
            <span className="hidden text-xs text-slate-500 sm:block">Analysis workspace</span>
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <ApiStatus />
          <nav className="flex items-center gap-1" aria-label="Primary navigation">
            {navItems.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/"
                ? pathname === "/"
                : pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={`flex h-10 items-center gap-2 rounded-md px-3 text-sm font-medium transition ${
                  active
                    ? "bg-teal-50 text-teal-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-ink"
                }`}
              >
                <Icon size={17} aria-hidden="true" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
          </nav>
        </div>
      </div>
    </header>
  );
}
