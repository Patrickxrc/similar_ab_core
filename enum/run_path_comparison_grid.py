#!/usr/bin/env python3
"""Batch-run compare_sim_ab_paths.py over a parameter grid and emit CSV."""

import argparse
import csv
import json
import subprocess
from itertools import product


def parse_int_pairs(s: str):
    out = []
    for part in s.split(','):
        a, b = part.split(':')
        out.append((int(a), int(b)))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--graphs', required=True, help='Comma-separated edge files')
    p.add_argument('--sim', default='0.2,0.3,0.4,0.5,0.6,0.7')
    p.add_argument('--ab', default='2:2,3:3,4:4,5:5,3:5,5:3,2:6,6:2')
    p.add_argument('--modes', default='both,sim_left,sim_right')
    p.add_argument('--metric', default='jaccard')
    p.add_argument('--out_csv', default='enum/path_compare_results.csv')
    args = p.parse_args()

    graphs = [x for x in args.graphs.split(',') if x]
    sims = [float(x) for x in args.sim.split(',') if x]
    ab_pairs = parse_int_pairs(args.ab)
    modes = [x for x in args.modes.split(',') if x]

    rows = []
    for graph, (a, b), sim, mode in product(graphs, ab_pairs, sims, modes):
        cmd = [
            'python', 'enum/compare_sim_ab_paths.py',
            graph, str(a), str(b), str(sim), mode, args.metric,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)

        row = {
            'graph': graph,
            'a': a,
            'b': b,
            'sim': sim,
            'mode': mode,
            'p1_final_left': data['path1_ab_then_sim']['final']['left_nodes'],
            'p1_final_right': data['path1_ab_then_sim']['final']['right_nodes'],
            'p1_final_edges': data['path1_ab_then_sim']['final']['edges'],
            'p2_final_left': data['path2_sim_then_ab']['final']['left_nodes'],
            'p2_final_right': data['path2_sim_then_ab']['final']['right_nodes'],
            'p2_final_edges': data['path2_sim_then_ab']['final']['edges'],
            'edge_jaccard': data['overlap']['edge_jaccard'],
            'left_jaccard': data['overlap']['left_node_jaccard'],
            'right_jaccard': data['overlap']['right_node_jaccard'],
            'same_edges': data['overlap']['exact_same_edges'],
            'same_left': data['overlap']['exact_same_left'],
            'same_right': data['overlap']['exact_same_right'],
        }
        rows.append(row)
        print(f"done: {graph} a={a} b={b} sim={sim} mode={mode}")

    fieldnames = list(rows[0].keys()) if rows else []
    with open(args.out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(args.out_csv)


if __name__ == '__main__':
    main()
