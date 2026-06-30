"""CLI for creating audited Stage 3 training CSV files."""

import argparse
import asyncio
import json
from pathlib import Path

from app.db.mongo import close_database
from app.pipeline.dataset_preparation import (
    analyze_dataset_quality,
    balance_training_rows,
    clean_training_rows,
    load_training_rows_from_mongodb,
    merge_training_datasets,
    read_training_csv,
    read_run_ids_file,
    write_training_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare clean text,label CSV data for Stage 3.",
    )
    parser.add_argument("--run-id", action="append", default=[], help="MongoDB runId; repeat to merge runs.")
    parser.add_argument("--run-ids-file", type=Path, help="JSON object mapping project names to runIds.")
    parser.add_argument("--input-csv", action="append", type=Path, default=[], help="Existing text,label CSV; repeat to merge files.")
    parser.add_argument("--output", type=Path, required=True, help="Clean, unbalanced output CSV.")
    parser.add_argument("--balance", choices=["downsample", "oversample"], help="Optional balancing strategy.")
    parser.add_argument("--balanced-output", type=Path, help="Balanced CSV path; defaults beside --output.")
    parser.add_argument("--target-count", type=int, help="Optional examples per class.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible balancing.")
    parser.add_argument("--report-output", type=Path, help="Quality report JSON path.")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    manifest_run_ids = read_run_ids_file(args.run_ids_file) if args.run_ids_file else []
    run_ids = list(dict.fromkeys([*args.run_id, *manifest_run_ids]))
    if not run_ids and not args.input_csv:
        raise SystemExit("Provide --run-id, --run-ids-file, or --input-csv.")

    datasets = [read_training_csv(path) for path in args.input_csv]
    if run_ids:
        try:
            datasets.append(await load_training_rows_from_mongodb(run_ids))
        finally:
            await close_database()

    merged = merge_training_datasets(datasets)
    source_report = analyze_dataset_quality(merged)
    cleaned = clean_training_rows(merged)
    clean_report = analyze_dataset_quality(cleaned)
    if not cleaned:
        raise SystemExit("No valid training rows remain after cleaning.")
    write_training_csv(args.output, cleaned)

    report: dict = {
        "source": source_report.to_dict(),
        "originalExport": clean_report.to_dict(),
        "originalPath": str(args.output.resolve()),
    }

    if args.balance:
        balanced = balance_training_rows(
            cleaned,
            args.balance,
            target_count=args.target_count,
            seed=args.seed,
        )
        balanced_path = args.balanced_output or args.output.with_name(
            f"{args.output.stem}-{args.balance}{args.output.suffix}"
        )
        write_training_csv(balanced_path, balanced)
        report["balancedExport"] = analyze_dataset_quality(balanced).to_dict()
        report["balancedPath"] = str(balanced_path.resolve())
        report["balanceMode"] = args.balance
        if args.balance == "oversample":
            report["experimentalWarning"] = (
                "Oversampling duplicates minority examples and is intended only for experimentation."
            )

    report_path = args.report_output or args.output.with_suffix(".quality.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
