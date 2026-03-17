#!/usr/bin/env python3
"""
Compare two filtering orders for similar (a,b)-core analysis:
Path 1: AB-core first, then SIM filtering
Path 2: SIM filtering first, then AB-core

Inputs: edge file, a, b, sim threshold, sim mode (both/sim_left/sim_right), metric (jaccard)
Outputs: summary metrics including overlap between final subgraphs.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

Edge = Tuple[str, str]  # (left, right)


def sort_ids(values: Iterable[str]) -> List[str]:
    def key_fn(x: str):
        return (0, int(x)) if x.isdigit() else (1, x)

    return sorted(values, key=key_fn)


@dataclass
class BiGraph:
    left_to_right: Dict[str, Set[str]]
    right_to_left: Dict[str, Set[str]]

    @property
    def edges(self) -> Set[Edge]:
        return {(l, r) for l, rs in self.left_to_right.items() for r in rs}

    @property
    def left_nodes(self) -> Set[str]:
        return set(self.left_to_right.keys())

    @property
    def right_nodes(self) -> Set[str]:
        return set(self.right_to_left.keys())


def read_bipartite_graph(edge_file: Path) -> BiGraph:
    left_to_right: Dict[str, Set[str]] = defaultdict(set)
    right_to_left: Dict[str, Set[str]] = defaultdict(set)

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

    # ensure both sides have explicit keys for deterministic reporting
    for l in list(left_to_right.keys()):
        _ = right_to_left  # keep symmetry by construction
    return BiGraph(dict(left_to_right), dict(right_to_left))


def induce_subgraph(g: BiGraph, kept_left: Set[str], kept_right: Set[str]) -> BiGraph:
    left_to_right: Dict[str, Set[str]] = {}
    right_to_left: Dict[str, Set[str]] = {r: set() for r in kept_right}

    for l in kept_left:
        neigh = g.left_to_right.get(l, set())
        filtered = {r for r in neigh if r in kept_right}
        left_to_right[l] = filtered
        for r in filtered:
            right_to_left.setdefault(r, set()).add(l)

    # prune isolated nodes from explicit dicts (keep only nodes appearing in edges)
    left_to_right = {l: rs for l, rs in left_to_right.items() if rs}
    right_to_left = {r: ls for r, ls in right_to_left.items() if ls}

    return BiGraph(left_to_right, right_to_left)


def ab_core(g: BiGraph, a: int, b: int) -> BiGraph:
    left_to_right = {l: set(rs) for l, rs in g.left_to_right.items()}
    right_to_left = {r: set(ls) for r, ls in g.right_to_left.items()}

    changed = True
    while changed:
        changed = False

        remove_left = [l for l, rs in left_to_right.items() if len(rs) < a]
        if remove_left:
            changed = True
            for l in remove_left:
                for r in list(left_to_right.get(l, set())):
                    if r in right_to_left:
                        right_to_left[r].discard(l)
                left_to_right.pop(l, None)

        remove_right = [r for r, ls in right_to_left.items() if len(ls) < b]
        if remove_right:
            changed = True
            for r in remove_right:
                for l in list(right_to_left.get(r, set())):
                    if l in left_to_right:
                        left_to_right[l].discard(r)
                right_to_left.pop(r, None)

        # cleanup empty adjacency caused by opposite-side removals
        empty_left = [l for l, rs in left_to_right.items() if not rs]
        for l in empty_left:
            left_to_right.pop(l, None)
            changed = True

        empty_right = [r for r, ls in right_to_left.items() if not ls]
        for r in empty_right:
            right_to_left.pop(r, None)
            changed = True

    return BiGraph(left_to_right, right_to_left)


def build_similarity_map(neighbor_map: Dict[str, Set[str]], threshold: float) -> Dict[str, List[str]]:
    keys = sort_ids(neighbor_map.keys())
    out = {k: [] for k in keys}
    for i, u in enumerate(keys):
        nu = neighbor_map[u]
        for v in keys[i + 1 :]:
            nv = neighbor_map[v]
            union = nu | nv
            if not union:
                continue
            jac = len(nu & nv) / len(union)
            if jac >= threshold:
                out[u].append(v)
                out[v].append(u)
    for k in out:
        out[k] = sort_ids(out[k])
    return out


def sim_json_by_mode(g: BiGraph, sim: float, mode: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    left_sim = build_similarity_map(g.left_to_right, sim)
    right_sim = build_similarity_map(g.right_to_left, sim)

    if mode == "both":
        return left_sim, right_sim
    if mode == "sim_left":
        return left_sim, {r: [] for r in sort_ids(g.right_nodes)}
    if mode == "sim_right":
        return {l: [] for l in sort_ids(g.left_nodes)}, right_sim
    raise ValueError(f"unknown mode: {mode}")


def apply_sim_filter(g: BiGraph, l_sim: Dict[str, List[str]], r_sim: Dict[str, List[str]], mode: str) -> BiGraph:
    if mode == "both":
        keep_left = {l for l, ns in l_sim.items() if ns}
        keep_right = {r for r, ns in r_sim.items() if ns}
    elif mode == "sim_left":
        keep_left = {l for l, ns in l_sim.items() if ns}
        keep_right = set(g.right_nodes)
    elif mode == "sim_right":
        keep_left = set(g.left_nodes)
        keep_right = {r for r, ns in r_sim.items() if ns}
    else:
        raise ValueError(f"unknown mode: {mode}")

    return induce_subgraph(g, keep_left, keep_right)


def jaccard(a: Set, b: Set) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    if not u:
        return 1.0
    return len(a & b) / len(u)


def summarize(g: BiGraph) -> Dict[str, int]:
    return {
        "left_nodes": len(g.left_nodes),
        "right_nodes": len(g.right_nodes),
        "edges": len(g.edges),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare AB->SIM and SIM->AB paths")
    parser.add_argument("edge_file")
    parser.add_argument("a", type=int)
    parser.add_argument("b", type=int)
    parser.add_argument("sim", type=float)
    parser.add_argument("mode", choices=["both", "sim_left", "sim_right"])
    parser.add_argument("metric", choices=["jaccard"])
    parser.add_argument("--out", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    g0 = read_bipartite_graph(Path(args.edge_file))

    # Path 1: AB -> SIM
    g1_ab = ab_core(g0, args.a, args.b)
    p1_lsim, p1_rsim = sim_json_by_mode(g1_ab, args.sim, args.mode)
    g1_final = apply_sim_filter(g1_ab, p1_lsim, p1_rsim, args.mode)

    # Path 2: SIM -> AB
    p2_lsim, p2_rsim = sim_json_by_mode(g0, args.sim, args.mode)
    g2_sim = apply_sim_filter(g0, p2_lsim, p2_rsim, args.mode)
    g2_final = ab_core(g2_sim, args.a, args.b)

    edge_overlap = jaccard(g1_final.edges, g2_final.edges)
    left_overlap = jaccard(g1_final.left_nodes, g2_final.left_nodes)
    right_overlap = jaccard(g1_final.right_nodes, g2_final.right_nodes)

    result = {
        "input": {
            "edge_file": args.edge_file,
            "a": args.a,
            "b": args.b,
            "sim": args.sim,
            "mode": args.mode,
            "metric": args.metric,
        },
        "path1_ab_then_sim": {
            "ab_core": summarize(g1_ab),
            "final": summarize(g1_final),
        },
        "path2_sim_then_ab": {
            "sim_filtered": summarize(g2_sim),
            "final": summarize(g2_final),
        },
        "overlap": {
            "edge_jaccard": edge_overlap,
            "left_node_jaccard": left_overlap,
            "right_node_jaccard": right_overlap,
            "exact_same_edges": g1_final.edges == g2_final.edges,
            "exact_same_left": g1_final.left_nodes == g2_final.left_nodes,
            "exact_same_right": g1_final.right_nodes == g2_final.right_nodes,
        },
    }

    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
