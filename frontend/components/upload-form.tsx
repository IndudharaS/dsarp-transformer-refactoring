"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  CircleAlert,
  FileSpreadsheet,
  LoaderCircle,
  UploadCloud,
  X,
} from "lucide-react";
import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { API_URL, getApiError } from "@/lib/api";

const systems = [
  { name: "Tika", version: "697d7c047daf1f661a4ed067bbc8f9c58bb6faa2", files: 1813 },
  { name: "Karaf", version: "5f5677d7395170208907f2f1655ae9fd9b3bff9e", files: 16892 },
  { name: "Struts", version: "d59aea5f5d6099ba09e894cb8810e00a37e112b1", files: 2462 },
  { name: "Logging-Log4j2", version: "4f474b32751f4ccad67424ca585612584440cd63", files: 3283 },
  { name: "Cassandra", version: "0269fd5665751e8a6d8eab852e0f66c142b10ee6", files: 4675 },
];

const fileCountFormatter = new Intl.NumberFormat("en-US");

const fileFields = [
  {
    name: "smellCharacteristics",
    label: "Smell characteristics",
    storedName: "smell-characteristics.csv",
    columns: "smellType, Severity, Size, Strength, InstabilityGap, AffectedElements, NumberOfEdges",
  },
  {
    name: "smellAffects",
    label: "Smell affects",
    storedName: "smell-affects.csv",
    columns: "from, to, fromId, toId",
  },
  {
    name: "componentMetrics",
    label: "Component metrics",
    storedName: "component-metrics.csv",
    columns: "name, FanIn, FanOut, LinesOfCode, InstabilityMetric, AbstractnessMetric, PageRank",
  },
] as const;

type FileFieldName = (typeof fileFields)[number]["name"];
type SelectedFiles = Partial<Record<FileFieldName, File>>;
type UploadResult = { runId: string; status: string; message: string };

function FileSelector({
  field,
  file,
  onChange,
}: {
  field: (typeof fileFields)[number];
  file?: File;
  onChange: (name: FileFieldName, file?: File) => void;
}) {
  const inputId = `file-${field.name}`;

  return (
    <div className="border-b border-line px-5 py-5 last:border-b-0 sm:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <FileSpreadsheet size={18} className="shrink-0 text-teal-600" />
            <h3 className="text-sm font-bold text-ink">{field.label}</h3>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Saved as <span className="font-mono">{field.storedName}</span>
          </p>
          <p className="mt-2 max-w-2xl truncate text-xs text-slate-400" title={field.columns}>
            Required: {field.columns}
          </p>
        </div>
        <div className="flex w-full items-center gap-2 lg:w-[360px]">
          <label
            htmlFor={inputId}
            className={`flex h-11 min-w-0 flex-1 cursor-pointer items-center rounded-md border px-3 text-sm transition ${
              file
                ? "border-teal-500 bg-teal-50 text-teal-700"
                : "border-dashed border-slate-300 bg-slate-50 text-slate-600 hover:border-teal-500"
            }`}
          >
            {file ? <Check size={17} className="mr-2 shrink-0" /> : <UploadCloud size={17} className="mr-2 shrink-0" />}
            <span className="truncate">{file?.name ?? "Choose CSV file"}</span>
          </label>
          <input
            id={inputId}
            className="sr-only"
            type="file"
            accept=".csv,text/csv"
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              onChange(field.name, event.target.files?.[0])
            }
          />
          {file && (
            <button
              type="button"
              onClick={() => onChange(field.name)}
              className="grid size-11 shrink-0 place-items-center rounded-md border border-line bg-white text-slate-500 hover:bg-slate-50 hover:text-ink"
              title={`Remove ${file.name}`}
            >
              <X size={17} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function UploadForm() {
  const [projectName, setProjectName] = useState("");
  const [systemName, setSystemName] = useState(systems[0].name);
  const [files, setFiles] = useState<SelectedFiles>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);

  const selectedSystem = useMemo(
    () => systems.find((system) => system.name === systemName) ?? systems[0],
    [systemName],
  );
  const allFilesSelected = fileFields.every((field) => files[field.name]);

  function updateFile(name: FileFieldName, file?: File) {
    setFiles((current) => ({ ...current, [name]: file }));
    setError("");
    setResult(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!projectName.trim() || !allFilesSelected) {
      setError("Enter a project name and select all three CSV files.");
      return;
    }

    const formData = new FormData();
    formData.append("projectName", projectName.trim());
    formData.append("systemName", selectedSystem.name);
    formData.append("version", selectedSystem.version);
    fileFields.forEach((field) => formData.append(field.name, files[field.name]!));

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(await getApiError(response));
      setResult((await response.json()) as UploadResult);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "The upload could not be completed.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <section className="overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="grid gap-5 border-b border-line p-5 sm:grid-cols-2 sm:p-6">
          <label className="block">
            <span className="mb-2 block text-sm font-bold text-ink">Project name</span>
            <input
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              placeholder="e.g. Tika architecture baseline"
              className="h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              required
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-bold text-ink">Software system</span>
            <select
              value={systemName}
              onChange={(event) => setSystemName(event.target.value)}
              className="h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            >
              {systems.map((system) => (
                <option key={system.name} value={system.name}>
                  {system.name} ({fileCountFormatter.format(system.files)} files)
                </option>
              ))}
            </select>
          </label>
          <div className="sm:col-span-2">
            <p className="text-xs font-bold uppercase text-slate-500">Version</p>
            <p className="mt-1 break-all font-mono text-xs text-slate-700">
              {selectedSystem.version}
            </p>
          </div>
        </div>
        <div>
          {fileFields.map((field) => (
            <FileSelector
              key={field.name}
              field={field}
              file={files[field.name]}
              onChange={updateFile}
            />
          ))}
        </div>
      </section>

      <aside className="h-fit rounded-lg border border-line bg-white p-5 shadow-panel sm:p-6">
        <h2 className="text-base font-bold text-ink">Run summary</h2>
        <dl className="mt-5 space-y-4 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">System</dt>
            <dd className="font-semibold text-ink">{selectedSystem.name}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Selected files</dt>
            <dd className="font-semibold text-ink">
              {Object.values(files).filter(Boolean).length} / 3
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Initial status</dt>
            <dd className="font-semibold text-ink">Uploaded</dd>
          </div>
        </dl>

        {error && (
          <div className="mt-5 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm leading-5 text-red-700">
            <CircleAlert size={17} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="mt-5 rounded-md border border-teal-500 bg-teal-50 p-4">
            <div className="flex items-center gap-2 text-sm font-bold text-teal-700">
              <Check size={18} />
              Upload stored
            </div>
            <p className="mt-2 break-all font-mono text-xs text-teal-700">
              {result.runId}
            </p>
            <Link
              href={`/runs/${encodeURIComponent(result.runId)}`}
              className="mt-4 flex items-center gap-2 text-sm font-bold text-teal-700 hover:text-teal-600"
            >
              Open analysis run <ArrowRight size={16} />
            </Link>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !projectName.trim() || !allFilesSelected}
          className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-bold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? (
            <>
              <LoaderCircle size={18} className="animate-spin" />
              Uploading
            </>
          ) : (
            <>
              <UploadCloud size={18} />
              Create analysis run
            </>
          )}
        </button>
      </aside>
    </form>
  );
}
