#!/usr/bin/env python3
"""Create intuitive plots for (a,b), sim, mode experiment outputs.

Supports both CSV schemas:
1) enum/run_path_comparison_grid.py output
2) enum/ppt_6case_summary.csv style summary
"""

import argparse
import csv
import math
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt


GRID_SCHEMA = {
    "a": "a",
    "b": "b",
    "sim": "sim",
    "mode": "mode",
    "p1_edges": "p1_final_edges",
    "p2_edges": "p2_final_edges",
    "edge_jaccard": "edge_jaccard",
    "edge_gap": "final_edge_path_gap",
}

ALGO_GRID_SCHEMA = {
    "a": "a",
    "b": "b",
    "sim": "sim",
    "algo": "algo",
    "final_edges": "final_edges",
    "r1_r2_edge_jaccard": "r1_r2_edge_jaccard",
    "r1_r2_gap": "r1_r2_gap",
}

PPT_SCHEMA = {
    "a": "alpha",
    "b": "beta",
    "sim": "sim",
    "mode": "mode",
    "p1_edges": "Path1_final_edges_AB_to_SIM",
    "p2_edges": "Path2_final_edges_SIM_to_AB",
    "edge_jaccard": "edge_jaccard",
    "edge_gap": "final_edge_path_gap",
}


def detect_schema(fieldnames):
    names = {normalize_key(x) for x in fieldnames}
    if set(ALGO_GRID_SCHEMA.values()).issubset(names):
        return "algo_grid", ALGO_GRID_SCHEMA
    if set(GRID_SCHEMA.values()).issubset(names):
        return "grid", GRID_SCHEMA
    if set(PPT_SCHEMA.values()).issubset(names):
        return "ppt", PPT_SCHEMA
    raise ValueError(
        "Unrecognized CSV schema. Need either legacy grid columns, "
        "algo-grid columns from run_path_comparison_grid.py, "
        "or ppt_6case_summary-style columns."
    )


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def normalize_key(key):
    if key is None:
        return ""
    return str(key).strip().lstrip("\ufeff")


def normalize_row(row):
    return {normalize_key(k): v for k, v in row.items()}


def load_rows(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        schema_type, schema = detect_schema(reader.fieldnames or [])
        if schema_type == "algo_grid":
            return load_rows_algo_grid(reader, schema)
        rows = []
        for raw in reader:
            row = normalize_row(raw)
            a = int(row[schema["a"]])
            b = int(row[schema["b"]])
            sim = safe_float(row[schema["sim"]])
            mode = row[schema["mode"]]
            rows.append(
                {
                    "ab": f"{a}:{b}",
                    "sim": sim,
                    "mode": mode,
                    "p1_edges": safe_float(row[schema["p1_edges"]]),
                    "p2_edges": safe_float(row[schema["p2_edges"]]),
                    "edge_jaccard": safe_float(row[schema["edge_jaccard"]]),
                    "edge_gap": safe_float(row[schema["edge_gap"]]),
                }
            )
    return rows


def load_rows_algo_grid(reader, schema):
    grouped = defaultdict(dict)
    for raw in reader:
        row = normalize_row(raw)
        a = int(row[schema["a"]])
        b = int(row[schema["b"]])
        sim = safe_float(row[schema["sim"]])
        algo = row[schema["algo"]]
        key = (f"{a}:{b}", sim)
        grouped[key][algo] = row

    rows = []
    for (ab, sim), by_algo in grouped.items():
        if "r1" not in by_algo or "r2" not in by_algo:
            continue

        r1 = by_algo["r1"]
        r2 = by_algo["r2"]
        rows.append(
            {
                "ab": ab,
                "sim": sim,
                "mode": "r1_vs_r2",
                "p1_edges": safe_float(r1[schema["final_edges"]]),
                "p2_edges": safe_float(r2[schema["final_edges"]]),
                "edge_jaccard": safe_float(
                    r1.get(schema["r1_r2_edge_jaccard"])
                    or r2.get(schema["r1_r2_edge_jaccard"])
                ),
                "edge_gap": safe_float(
                    r1.get(schema["r1_r2_gap"]) or r2.get(schema["r1_r2_gap"])
                ),
            }
        )
    return rows


def average_by_mode_ab_sim(rows, metric):
    bucket = defaultdict(list)
    for r in rows:
        key = (r["mode"], r["ab"], r["sim"])
        bucket[key].append(r[metric])

    out = {}
    for key, vals in bucket.items():
        clean = [v for v in vals if not math.isnan(v)]
        out[key] = sum(clean) / len(clean) if clean else math.nan
    return out


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def choose_default_csv():
    """Pick a sensible default input CSV when user doesn't pass one."""
    candidates = [
        "enum/path_compare_results.csv",
        "enum/ppt_6case_summary.csv",
        "path_compare_results.csv",
        "ppt_6case_summary.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def plot_heatmaps(rows, out_dir):
    agg = average_by_mode_ab_sim(rows, "edge_jaccard")
    modes = sorted({r["mode"] for r in rows})
    abs_ = sorted({r["ab"] for r in rows})
    sims = sorted({r["sim"] for r in rows})

    fig, axes = plt.subplots(
        1,
        len(modes),
        figsize=(5 * max(1, len(modes)), 4),
        squeeze=False,
        constrained_layout=True,
    )
    for i, mode in enumerate(modes):
        ax = axes[0][i]
        matrix = []
        for ab in abs_:
            matrix.append([agg.get((mode, ab, sim), math.nan) for sim in sims])

        im = ax.imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")
        ax.set_title(f"mode={mode}")
        ax.set_xticks(range(len(sims)))
        ax.set_xticklabels([f"{x:.2f}" for x in sims], rotation=45, ha="right")
        ax.set_yticks(range(len(abs_)))
        ax.set_yticklabels(abs_)
        ax.set_xlabel("sim threshold")
        if i == 0:
            ax.set_ylabel("(a,b)")

    fig.suptitle("Path1 vs Path2 edge Jaccard (higher = closer)")
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.025, pad=0.04)
    out = os.path.join(out_dir, "edge_jaccard_heatmaps.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_gap_curves(rows, out_dir):
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["mode"], r["ab"])].append(r)

    fig, ax = plt.subplots(figsize=(8, 5))
    for (mode, ab), items in sorted(grouped.items()):
        items.sort(key=lambda x: x["sim"])
        xs = [x["sim"] for x in items]
        ys = [x["edge_gap"] for x in items]
        ax.plot(xs, ys, marker="o", linewidth=1.5, label=f"{mode} | {ab}")

    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("sim threshold")
    ax.set_ylabel("final_edge_path_gap")
    ax.set_title("Path gap vs sim (1.0 means maximal difference)")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    out = os.path.join(out_dir, "final_edge_gap_curves.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def plot_path_edges(rows, out_dir):
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["mode"], r["ab"])].append(r)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharex=True)
    ax1, ax2 = axes

    for (mode, ab), items in sorted(grouped.items()):
        items.sort(key=lambda x: x["sim"])
        xs = [x["sim"] for x in items]
        p1 = [x["p1_edges"] for x in items]
        p2 = [x["p2_edges"] for x in items]
        label = f"{mode} | {ab}"
        ax1.plot(xs, p1, marker="o", linewidth=1.5, label=label)
        ax2.plot(xs, p2, marker="o", linewidth=1.5, label=label)

    ax1.set_title("Path1 final edges (AB -> SIM)")
    ax2.set_title("Path2 final edges (SIM -> AB)")
    for ax in axes:
        ax.set_xlabel("sim threshold")
        ax.set_ylabel("edges")
        ax.grid(True, alpha=0.25)

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    out = os.path.join(out_dir, "path1_path2_edge_curves.png")
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Visualize outputs from path-comparison experiments. "
            "If csv is omitted, the script auto-detects a common default file."
        )
    )
    parser.add_argument("csv", nargs="?", help="Input CSV file")
    parser.add_argument(
        "--out_dir", default="enum/figures", help="Directory for generated PNG files"
    )
    parser.add_argument(
        "--list-defaults",
        action="store_true",
        help="Print default CSV candidates and exit",
    )
    parser.add_argument(
        "--debug-schema",
        action="store_true",
        help="Print CSV headers and detected schema, then continue plotting",
    )
    args = parser.parse_args()

    default_candidates = [
        "enum/path_compare_results.csv",
        "enum/ppt_6case_summary.csv",
        "path_compare_results.csv",
        "ppt_6case_summary.csv",
    ]
    if args.list_defaults:
        for p in default_candidates:
            print(p)
        return

    input_csv = args.csv or choose_default_csv()
    if not input_csv:
        parser.print_help()
        print(
            "\nError: missing csv input and no default CSV found.\n"
            "Try: python enum/plot_path_comparison.py enum/ppt_6case_summary.csv",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.debug_schema:
        with open(input_csv, newline="") as f:
            reader = csv.DictReader(f)
            headers = [normalize_key(x) for x in (reader.fieldnames or [])]
            schema_type, _ = detect_schema(headers)
            print(f"headers={headers}")
            print(f"detected_schema={schema_type}")

    rows = load_rows(input_csv)
    if not rows:
        raise ValueError(f"CSV has no data rows: {input_csv}")

    ensure_dir(args.out_dir)
    outputs = [
        plot_heatmaps(rows, args.out_dir),
        plot_gap_curves(rows, args.out_dir),
        plot_path_edges(rows, args.out_dir),
    ]

    print(f"input_csv={input_csv}")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
