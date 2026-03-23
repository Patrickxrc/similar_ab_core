#!/usr/bin/env python3
"""Batch-run r1/r2/r3/r4 (LEFT-SIM-only) over a parameter grid and emit CSV."""

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
    p.add_argument('--sim', default='0.1,0.12,0.14,0.16,0.18,0.2')
    p.add_argument('--ab', default='1:1,1:2,2:1,2:2,2:3,3:3')
    p.add_argument('--algos', default='r1,r2,r3,r4')
    p.add_argument('--metric', default='jaccard')
    p.add_argument('--max_iter', type=int, default=20)
    p.add_argument('--ab_step', type=int, default=1)
    p.add_argument('--sim_step', type=float, default=0.02)
    p.add_argument('--out_csv', default='enum/path_compare_results.csv')
    args = p.parse_args()

    graphs = [x for x in args.graphs.split(',') if x]
    sims = [float(x) for x in args.sim.split(',') if x]
    ab_pairs = parse_int_pairs(args.ab)
    algos = [x for x in args.algos.split(',') if x]

    rows = []
    for graph, (a, b), sim, algo in product(graphs, ab_pairs, sims, algos):
        cmd = [
            'python', 'enum/compare_sim_ab_paths.py',
            graph, str(a), str(b), str(sim), args.metric,
            '--algo', algo,
            '--max_iter', str(args.max_iter),
            '--ab_step', str(args.ab_step),
            '--sim_step', str(args.sim_step),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)

        row = {
            'graph': graph,
            'a': a,
            'b': b,
            'sim': sim,
            'algo': algo,
            'final_left': data['final']['left_nodes'],
            'final_right': data['final']['right_nodes'],
            'final_edges': data['final']['edges'],
            'iters': len(data.get('trace', [])),
        }

        if 'r1_r2_compare' in data:
            c = data['r1_r2_compare']
            row.update({
                'r1_r2_edge_jaccard': c['edge_jaccard'],
                'r1_r2_left_jaccard': c['left_jaccard'],
                'r1_r2_right_jaccard': c['right_jaccard'],
                'r1_edges': c['r1_edges'],
                'r2_edges': c['r2_edges'],
                'r1_r2_gap': c['final_edge_path_gap'],
            })

        rows.append(row)
        print(f"done: {graph} a={a} b={b} sim={sim} algo={algo}")

    fieldnames = sorted({k for r in rows for k in r.keys()}) if rows else []
    with open(args.out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(args.out_csv)


if __name__ == '__main__':
    main()
