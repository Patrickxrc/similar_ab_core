#!/usr/bin/env python3
"""Run similar (a,b)-core style algorithms with LEFT-side SIM only.

Algorithms:
- r1: AB -> SIM
- r2: SIM -> AB
- r3: iterative (SIM -> AB), update (a,b) each round
- r4: iterative (AB -> SIM), update sim threshold each round
"""

from __future__ import annotations

import argparse
import json
import math
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


def build_left_sim_only(g: BiGraph, sim: float) -> Dict[str, List[str]]:
    return build_similarity_map(g.left_to_right, sim)


def apply_left_sim_filter(g: BiGraph, left_sim: Dict[str, List[str]]) -> BiGraph:
    keep_left = {l for l, ns in left_sim.items() if ns}
    keep_right = set(g.right_nodes)
    return induce_subgraph(g, keep_left, keep_right)


def jaccard(a: Set, b: Set) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    if not u:
        return 1.0
    return len(a & b) / len(u)


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def summarize(g: BiGraph) -> Dict[str, int]:
    return {
        "left_nodes": len(g.left_nodes),
        "right_nodes": len(g.right_nodes),
        "edges": len(g.edges),
    }


def graph_signature(g: BiGraph) -> Tuple[Tuple[str, ...], Tuple[str, ...], int]:
    return (tuple(sort_ids(g.left_nodes)), tuple(sort_ids(g.right_nodes)), len(g.edges))


def run_r1(g0: BiGraph, a: int, b: int, sim: float):
    g_ab = ab_core(g0, a, b)
    lsim = build_left_sim_only(g_ab, sim)
    g_final = apply_left_sim_filter(g_ab, lsim)
    trace = [{"iter": 1, "a": a, "b": b, "sim": sim, "after_ab": summarize(g_ab), "after_sim": summarize(g_final)}]
    return g_final, trace


def run_r2(g0: BiGraph, a: int, b: int, sim: float):
    lsim = build_left_sim_only(g0, sim)
    g_sim = apply_left_sim_filter(g0, lsim)
    g_final = ab_core(g_sim, a, b)
    trace = [{"iter": 1, "a": a, "b": b, "sim": sim, "after_sim": summarize(g_sim), "after_ab": summarize(g_final)}]
    return g_final, trace


def run_r3(g0: BiGraph, a: int, b: int, sim: float, max_iter: int, ab_step: int):
    g = g0
    a_t, b_t = a, b
    trace = []
    for it in range(1, max_iter + 1):
        lsim = build_left_sim_only(g, sim)
        g_sim = apply_left_sim_filter(g, lsim)
        g_next = ab_core(g_sim, a_t, b_t)
        trace.append({"iter": it, "a": a_t, "b": b_t, "sim": sim, "after_sim": summarize(g_sim), "after_ab": summarize(g_next)})

        if graph_signature(g_next) == graph_signature(g):
            g = g_next
            break
        g = g_next
        a_t = max(1, a_t + ab_step)
        b_t = max(1, b_t + ab_step)
    return g, trace


def run_r4(g0: BiGraph, a: int, b: int, sim: float, max_iter: int, sim_step: float):
    g = g0
    tau = sim
    trace = []
    for it in range(1, max_iter + 1):
        g_ab = ab_core(g, a, b)
        lsim = build_left_sim_only(g_ab, tau)
        g_next = apply_left_sim_filter(g_ab, lsim)
        trace.append({"iter": it, "a": a, "b": b, "sim": tau, "after_ab": summarize(g_ab), "after_sim": summarize(g_next)})

        if graph_signature(g_next) == graph_signature(g):
            g = g_next
            break
        g = g_next
        tau = min(1.0, tau + sim_step)
    return g, trace


def main():
    parser = argparse.ArgumentParser(description="Run r1/r2/r3/r4 with LEFT-SIM-only")
    parser.add_argument("edge_file")
    parser.add_argument("a", type=int)
    parser.add_argument("b", type=int)
    parser.add_argument("sim", type=float)
    parser.add_argument("metric", choices=["jaccard"])
    parser.add_argument("--algo", choices=["r1", "r2", "r3", "r4"], default="r1")
    parser.add_argument("--max_iter", type=int, default=20)
    parser.add_argument("--ab_step", type=int, default=1)
    parser.add_argument("--sim_step", type=float, default=0.02)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    g0 = read_bipartite_graph(Path(args.edge_file))

    if args.algo == "r1":
        g_final, trace = run_r1(g0, args.a, args.b, args.sim)
    elif args.algo == "r2":
        g_final, trace = run_r2(g0, args.a, args.b, args.sim)
    elif args.algo == "r3":
        g_final, trace = run_r3(g0, args.a, args.b, args.sim, args.max_iter, args.ab_step)
    else:
        g_final, trace = run_r4(g0, args.a, args.b, args.sim, args.max_iter, args.sim_step)

    result = {
        "input": {
            "edge_file": args.edge_file,
            "a": args.a,
            "b": args.b,
            "sim": args.sim,
            "metric": args.metric,
            "algo": args.algo,
            "sim_mode": "sim_left_fixed",
            "max_iter": args.max_iter,
            "ab_step": args.ab_step,
            "sim_step": args.sim_step,
        },
        "final": summarize(g_final),
        "trace": trace,
    }

    # include r1/r2 overlap only when one of them is requested for quick compare
    if args.algo in {"r1", "r2"}:
        g_r1, _ = run_r1(g0, args.a, args.b, args.sim)
        g_r2, _ = run_r2(g0, args.a, args.b, args.sim)
        result["r1_r2_compare"] = {
            "edge_jaccard": jaccard(g_r1.edges, g_r2.edges),
            "left_jaccard": jaccard(g_r1.left_nodes, g_r2.left_nodes),
            "right_jaccard": jaccard(g_r1.right_nodes, g_r2.right_nodes),
            "r1_edges": len(g_r1.edges),
            "r2_edges": len(g_r2.edges),
            "final_edge_path_gap": safe_ratio(abs(len(g_r1.edges) - len(g_r2.edges)), max(1, len(g_r1.edges), len(g_r2.edges))),
        }

    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
