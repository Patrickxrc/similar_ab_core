#!/usr/bin/env python3
"""Diagnose CSV compatibility for enum/plot_path_comparison.py without matplotlib."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


GRID_REQUIRED = {
    "a", "b", "sim", "mode", "p1_final_edges", "p2_final_edges", "edge_jaccard", "final_edge_path_gap"
}
ALGO_GRID_REQUIRED = {
    "a", "b", "sim", "algo", "final_edges", "r1_r2_edge_jaccard", "r1_r2_gap"
}
PPT_REQUIRED = {
    "alpha", "beta", "sim", "mode", "Path1_final_edges_AB_to_SIM", "Path2_final_edges_SIM_to_AB", "edge_jaccard", "final_edge_path_gap"
}


def norm(k: str | None) -> str:
    return (k or "").strip().lstrip("\ufeff")


def detect(headers: set[str]) -> str:
    if ALGO_GRID_REQUIRED.issubset(headers):
        return "algo_grid"
    if GRID_REQUIRED.issubset(headers):
        return "legacy_grid"
    if PPT_REQUIRED.issubset(headers):
        return "ppt_summary"
    return "unknown"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--head", type=int, default=3)
    args = p.parse_args()

    path = Path(args.csv_path)
    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [norm(h) for h in (reader.fieldnames or [])]
        schema = detect(set(headers))
        rows = []
        for i, row in enumerate(reader):
            if i >= args.head:
                break
            rows.append({norm(k): v for k, v in row.items()})

    print(json.dumps({
        "csv": str(path),
        "schema": schema,
        "headers": headers,
        "head_rows": rows,
    }, ensure_ascii=False, indent=2))

    if schema == "unknown":
        print("\nSuggestion: check delimiter/encoding/header names.")
    else:
        print("\nSuggested plot command:")
        print(f"python enum/plot_path_comparison.py {path} --debug-schema --out_dir enum/figures_facebook")


if __name__ == "__main__":
    main()
