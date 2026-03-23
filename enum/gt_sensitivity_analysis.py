#!/usr/bin/env python3
"""Sensitivity analysis over GT construction thresholds.

For each min_user_interactions value:
1) Build GT communities via build_gt_communities.py
2) Run r1/r2/r3/r4 under fixed (a,b,sim)
3) Evaluate each algorithm output against GT with edge-level metrics
4) Write a unified CSV summary
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from compare_sim_ab_paths import read_bipartite_graph, run_r1, run_r2, run_r3, run_r4

Edge = Tuple[str, str]


def parse_ab_list(raw: str) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        a, b = part.split(':')
        out.append((int(a), int(b)))
    if not out:
        raise ValueError("--ab must contain at least one pair like 40:20")
    return out


def parse_float_list(raw: str) -> List[float]:
    vals = [float(x) for x in raw.split(',') if x.strip()]
    if not vals:
        raise ValueError("float list is empty")
    return vals


def parse_int_list(raw: str) -> List[int]:
    vals = [int(x) for x in raw.split(',') if x.strip()]
    if not vals:
        raise ValueError("int list is empty")
    return vals


def build_gt(
    edges: Path,
    out_json: Path,
    min_user_interactions: int,
    meta_source: str,
    meta_config: str,
    meta_jsonl: str | None,
    min_users: int,
    min_items: int,
    max_labels_per_item: int,
    max_communities: int,
) -> Dict:
    cmd = [
        "python",
        "enum/build_gt_communities.py",
        "--edges",
        str(edges),
        "--out",
        str(out_json),
        "--meta_source",
        meta_source,
        "--meta_config",
        meta_config,
        "--min_user_interactions",
        str(min_user_interactions),
        "--min_users",
        str(min_users),
        "--min_items",
        str(min_items),
        "--max_labels_per_item",
        str(max_labels_per_item),
        "--max_communities",
        str(max_communities),
    ]

    if meta_source == "local":
        if not meta_jsonl:
            raise ValueError("--meta_jsonl is required when --meta_source local")
        cmd.extend(["--meta_jsonl", meta_jsonl])

    subprocess.run(cmd, check=True)
    return json.loads(out_json.read_text())


def gt_edge_set(gt_payload: Dict, graph_edges: Set[Edge], left_to_right: Dict[str, Set[str]]) -> Set[Edge]:
    gt_edges: Set[Edge] = set()
    for c in gt_payload.get("communities", []):
        U = set(c.get("U", []))
        V = set(c.get("V", []))
        for u in U:
            for v in left_to_right.get(u, set()):
                if v in V:
                    gt_edges.add((u, v))
    # keep only edges that exist in graph universe
    return gt_edges & graph_edges


def eval_edges(pred_edges: Set[Edge], gt_edges: Set[Edge], universe_size: int) -> Dict[str, float | int]:
    tp = len(pred_edges & gt_edges)
    fp = len(pred_edges - gt_edges)
    fn = len(gt_edges - pred_edges)
    tn = max(0, universe_size - tp - fp - fn)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / universe_size if universe_size else 0.0
    jaccard = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": jaccard,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="GT sensitivity analysis for r1/r2/r3/r4")
    p.add_argument("--edges", required=True)
    p.add_argument("--meta_source", choices=["hf", "local"], default="local")
    p.add_argument("--meta_config", default="raw_meta_Electronics")
    p.add_argument("--meta_jsonl", default=None)

    p.add_argument("--gt_min_user_interactions", default="1,2,3,4")
    p.add_argument("--gt_min_users", type=int, default=20)
    p.add_argument("--gt_min_items", type=int, default=20)
    p.add_argument("--gt_max_labels_per_item", type=int, default=3)
    p.add_argument("--gt_max_communities", type=int, default=200)

    p.add_argument("--ab", default="40:20,50:25")
    p.add_argument("--sim", default="0.24,0.26")
    p.add_argument("--max_iter", type=int, default=20)
    p.add_argument("--ab_step", type=int, default=0, help="for r3; set 0 for fixed-parameter iteration")
    p.add_argument("--sim_step", type=float, default=0.0, help="for r4; set 0 for fixed-parameter iteration")

    p.add_argument("--out_csv", default="enum/gt_sensitivity_results.csv")
    p.add_argument("--gt_out_dir", default="data/gt")

    args = p.parse_args()

    edges_path = Path(args.edges)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    gt_dir = Path(args.gt_out_dir)
    gt_dir.mkdir(parents=True, exist_ok=True)

    ab_list = parse_ab_list(args.ab)
    sim_list = parse_float_list(args.sim)
    min_ui_list = parse_int_list(args.gt_min_user_interactions)

    g0 = read_bipartite_graph(edges_path)
    universe_edges = g0.edges
    universe_size = len(g0.left_nodes) * len(g0.right_nodes)

    rows: List[Dict[str, str | int | float]] = []

    for min_ui in min_ui_list:
        gt_path = gt_dir / f"gt_mui_{min_ui}.json"
        gt_payload = build_gt(
            edges=edges_path,
            out_json=gt_path,
            min_user_interactions=min_ui,
            meta_source=args.meta_source,
            meta_config=args.meta_config,
            meta_jsonl=args.meta_jsonl,
            min_users=args.gt_min_users,
            min_items=args.gt_min_items,
            max_labels_per_item=args.gt_max_labels_per_item,
            max_communities=args.gt_max_communities,
        )

        gt_edges = gt_edge_set(gt_payload, universe_edges, g0.left_to_right)

        gt_meta = gt_payload.get("meta", {})
        gt_n_comm = int(gt_meta.get("num_communities", len(gt_payload.get("communities", []))))

        for a, b in ab_list:
            for sim in sim_list:
                algo_out: Dict[str, Tuple[Set[Edge], int]] = {}

                g_r1, t1 = run_r1(g0, a, b, sim)
                algo_out["r1"] = (g_r1.edges, len(t1))

                g_r2, t2 = run_r2(g0, a, b, sim)
                algo_out["r2"] = (g_r2.edges, len(t2))

                g_r3, t3 = run_r3(g0, a, b, sim, args.max_iter, args.ab_step)
                algo_out["r3"] = (g_r3.edges, len(t3))

                g_r4, t4 = run_r4(g0, a, b, sim, args.max_iter, args.sim_step)
                algo_out["r4"] = (g_r4.edges, len(t4))

                for algo, (pred_edges, iters) in algo_out.items():
                    m = eval_edges(pred_edges, gt_edges, universe_size)
                    rows.append(
                        {
                            "gt_min_user_interactions": min_ui,
                            "gt_num_communities": gt_n_comm,
                            "gt_edges": len(gt_edges),
                            "a": a,
                            "b": b,
                            "sim": sim,
                            "algo": algo,
                            "iters": iters,
                            "pred_edges": len(pred_edges),
                            **m,
                        }
                    )

    fieldnames = [
        "gt_min_user_interactions",
        "gt_num_communities",
        "gt_edges",
        "a",
        "b",
        "sim",
        "algo",
        "iters",
        "pred_edges",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "jaccard",
        "tp",
        "fp",
        "fn",
        "tn",
    ]

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(out_csv)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
