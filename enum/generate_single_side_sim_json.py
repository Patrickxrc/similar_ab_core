#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path


def norm_sim(sim: float) -> str:
    return f"{sim:.6f}"


def sort_ids(values):
    def k(x):
        return (0, int(x)) if x.isdigit() else (1, x)
    return sorted(values, key=k)


def build_similarity_map(neighbor_map: dict[str, set[str]], threshold: float) -> dict[str, list[str]]:
    keys = sort_ids(list(neighbor_map.keys()))
    result = {k: [] for k in keys}
    for i, u in enumerate(keys):
        nu = neighbor_map[u]
        for v in keys[i + 1:]:
            nv = neighbor_map[v]
            union = nu | nv
            if not union:
                continue
            jac = len(nu & nv) / len(union)
            if jac >= threshold:
                result[u].append(v)
                result[v].append(u)
    for k in result:
        result[k] = sort_ids(result[k])
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate sim_left/sim_right JSON neighbor files from bipartite edge list")
    parser.add_argument("edge_file", help="Edge list file, each line: <left_vertex> <right_vertex>")
    parser.add_argument("sim_threshold", type=float, help="Similarity threshold")
    parser.add_argument("metric", choices=["jaccard"], help="Similarity metric")
    args = parser.parse_args()

    edge_file = Path(args.edge_file)
    if not edge_file.exists():
        raise FileNotFoundError(f"edge file not found: {edge_file}")

    left_to_right = defaultdict(set)
    right_to_left = defaultdict(set)

    with edge_file.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("%"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            l, r = parts[0], parts[1]
            left_to_right[l].add(r)
            right_to_left[r].add(l)

    left_ids = sort_ids(list(left_to_right.keys()))
    right_ids = sort_ids(list(right_to_left.keys()))

    left_sim = build_similarity_map(left_to_right, args.sim_threshold)
    right_sim = build_similarity_map(right_to_left, args.sim_threshold)

    # single-side definitions
    sim_left_vl = left_sim
    sim_left_vr = {r: [] for r in right_ids}

    sim_right_vl = {l: [] for l in left_ids}
    sim_right_vr = right_sim

    sim_str = norm_sim(args.sim_threshold)
    prefix = str(edge_file)

    outputs = {
        f"{prefix}cpp_nei_sim_left_VL{sim_str}.json": sim_left_vl,
        f"{prefix}cpp_nei_sim_left_VR{sim_str}.json": sim_left_vr,
        f"{prefix}cpp_nei_sim_right_VL{sim_str}.json": sim_right_vl,
        f"{prefix}cpp_nei_sim_right_VR{sim_str}.json": sim_right_vr,
    }

    for out_path, payload in outputs.items():
        with open(out_path, "w") as f:
            json.dump(payload, f)
        print(out_path)


if __name__ == "__main__":
    main()
