#!/usr/bin/env python3
"""Prepare SNAP Facebook circles into bipartite edges + GT JSON.

This utility converts user-labeled circle files (`*.circles`) into:
1) a bipartite edge list: (user_id, circle_id)
2) an overlapping GT communities JSON with U/V sets

Why this format:
- Existing r1/r2/r3/r4 scripts in this repo consume bipartite graphs.
- SNAP circles are human-curated groups; this keeps that signal as GT.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_circle_file(path: Path, include_ego: bool) -> List[Tuple[str, Set[str], str]]:
    ego = path.stem
    out: List[Tuple[str, Set[str], str]] = []
    with path.open("r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            circle_name = parts[0]
            members = set(parts[1:])
            if include_ego:
                members.add(ego)
            circle_id = f"fb_circle::{ego}::{circle_name}"
            label = f"{ego}:{circle_name}"
            out.append((circle_id, members, label))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Facebook circles to bipartite + GT JSON")
    parser.add_argument("--circles_dir", required=True, help="Directory containing SNAP *.circles files")
    parser.add_argument("--out_edges", required=True, help="Output bipartite edge file path")
    parser.add_argument("--out_gt", required=True, help="Output GT communities JSON path")
    parser.add_argument("--min_users", type=int, default=5, help="Minimum users per circle to keep")
    parser.add_argument("--include_ego", action="store_true", help="Add ego user into each owned circle")
    args = parser.parse_args()

    circles_dir = Path(args.circles_dir)
    files = sorted(circles_dir.glob("*.circles"))
    if not files:
        raise SystemExit(f"No .circles files found under: {circles_dir}")

    edges: Set[Tuple[str, str]] = set()
    communities: List[Dict[str, object]] = []

    for fp in files:
        parsed = parse_circle_file(fp, include_ego=args.include_ego)
        for circle_id, members, label in parsed:
            if len(members) < args.min_users:
                continue
            for u in members:
                edges.add((u, circle_id))
            communities.append(
                {
                    "label": label,
                    "U": sorted(members),
                    "V": [circle_id],
                }
            )

    out_edges = Path(args.out_edges)
    out_gt = Path(args.out_gt)
    out_edges.parent.mkdir(parents=True, exist_ok=True)
    out_gt.parent.mkdir(parents=True, exist_ok=True)

    with out_edges.open("w", encoding="utf-8") as f:
        for u, c in sorted(edges):
            f.write(f"{u} {c}\n")

    payload = {
        "meta": {
            "source": "SNAP ego-Facebook circles",
            "circles_dir": str(circles_dir),
            "files": len(files),
            "min_users": args.min_users,
            "include_ego": args.include_ego,
            "communities": len(communities),
            "edges": len(edges),
        },
        "communities": communities,
    }
    with out_gt.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "out_edges": str(out_edges),
                "out_gt": str(out_gt),
                "communities": len(communities),
                "edges": len(edges),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
