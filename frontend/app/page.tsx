import { UploadForm } from "@/components/upload-form";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase text-teal-700">New analysis run</p>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">Upload DSARP datasets</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Choose a supported system and attach the three CSV exports required to
          create an analysis run.
        </p>
      </div>
      <UploadForm />
    </div>
  );
}
