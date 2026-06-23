import { DatabaseRecords } from "@/components/database-records";
import { LoaderCircle } from "lucide-react";
import { Suspense } from "react";

export default function DatabasePage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase text-teal-700">Storage verification</p>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">Database records</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Confirm that each run exists in MongoDB and has matching uploaded file metadata.
        </p>
      </div>
      <Suspense
        fallback={
          <div className="flex min-h-48 items-center justify-center gap-2 rounded-lg border border-line bg-white text-sm text-slate-500 shadow-panel">
            <LoaderCircle size={18} className="animate-spin" />
            Loading database view
          </div>
        }
      >
        <DatabaseRecords />
      </Suspense>
    </div>
  );
}
