#!/usr/bin/env python3
"""Build overlapping community ground-truth from Amazon metadata labels.

Community definition (label-centric):
- V_label: items containing label
- U_label: users interacting with >= min_user_interactions items in V_label

Output JSON is used for community detection evaluation (r1/r2/r3/r4 vs GT).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


def parse_edge_line(line: str) -> Tuple[str, str] | None:
    parts = line.strip().split()
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def read_edges(path: Path):
    user_to_items: Dict[str, Set[str]] = defaultdict(set)
    item_to_users: Dict[str, Set[str]] = defaultdict(set)

    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("%"):
                continue
            pair = parse_edge_line(line)
            if not pair:
                continue
            u, i = pair
            user_to_items[u].add(i)
            item_to_users[i].add(u)

    return user_to_items, item_to_users


def flatten_categories(cats) -> List[str]:
    out: List[str] = []

    def dfs(x):
        if x is None:
            return
        if isinstance(x, str):
            s = x.strip()
            if s:
                out.append(s)
            return
        if isinstance(x, (list, tuple)):
            for y in x:
                dfs(y)

    dfs(cats)
    # dedupe keep order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            deduped.append(x)
            seen.add(x)
    return deduped


def iter_meta_from_hf(dataset_name: str, config: str):
    from datasets import load_dataset

    ds = load_dataset(
        dataset_name,
        config,
        split="full",
        streaming=True,
        trust_remote_code=True,
    )
    for row in ds:
        yield row


def iter_meta_from_local(jsonl_path: Path):
    with jsonl_path.open() as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def main():
    p = argparse.ArgumentParser(description="Build overlapping GT communities from item labels")
    p.add_argument("--edges", required=True, help="Edge file path (user item per line)")
    p.add_argument("--out", default="data/gt/gt_communities.json")

    p.add_argument("--meta_source", choices=["hf", "local"], default="hf")
    p.add_argument("--hf_dataset", default="McAuley-Lab/Amazon-Reviews-2023")
    p.add_argument("--meta_config", default="raw_meta_Electronics")
    p.add_argument("--meta_jsonl", default=None, help="Used when meta_source=local")

    p.add_argument("--max_labels_per_item", type=int, default=3)
    p.add_argument("--min_user_interactions", type=int, default=2)
    p.add_argument("--min_users", type=int, default=20)
    p.add_argument("--min_items", type=int, default=20)
    p.add_argument("--max_communities", type=int, default=500)

    args = p.parse_args()

    edge_path = Path(args.edges)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    user_to_items, item_to_users = read_edges(edge_path)
    target_items = set(item_to_users.keys())

    item_to_labels: Dict[str, List[str]] = {}

    if args.meta_source == "hf":
        meta_iter = iter_meta_from_hf(args.hf_dataset, args.meta_config)
    else:
        if not args.meta_jsonl:
            raise ValueError("--meta_jsonl is required when --meta_source local")
        meta_iter = iter_meta_from_local(Path(args.meta_jsonl))

    for row in meta_iter:
        asin = row.get("parent_asin") or row.get("asin")
        if asin not in target_items:
            continue
        labels = flatten_categories(row.get("categories"))
        if not labels:
            continue
        item_to_labels[asin] = labels[: max(1, args.max_labels_per_item)]

    label_to_items: Dict[str, Set[str]] = defaultdict(set)
    for item, labels in item_to_labels.items():
        for lb in labels:
            label_to_items[lb].add(item)

    communities = []
    for lb, items in label_to_items.items():
        if len(items) < args.min_items:
            continue

        users = []
        for u, u_items in user_to_items.items():
            inter = len(u_items & items)
            if inter >= args.min_user_interactions:
                users.append(u)

        if len(users) < args.min_users:
            continue

        communities.append(
            {
                "label": lb,
                "U": sorted(users),
                "V": sorted(items),
                "num_users": len(users),
                "num_items": len(items),
            }
        )

    communities.sort(key=lambda x: (x["num_users"] * x["num_items"]), reverse=True)
    communities = communities[: args.max_communities]

    payload = {
        "meta": {
            "edges": str(edge_path),
            "meta_source": args.meta_source,
            "hf_dataset": args.hf_dataset if args.meta_source == "hf" else None,
            "meta_config": args.meta_config if args.meta_source == "hf" else None,
            "meta_jsonl": args.meta_jsonl if args.meta_source == "local" else None,
            "max_labels_per_item": args.max_labels_per_item,
            "min_user_interactions": args.min_user_interactions,
            "min_users": args.min_users,
            "min_items": args.min_items,
            "max_communities": args.max_communities,
            "num_edge_users": len(user_to_items),
            "num_edge_items": len(item_to_users),
            "num_labeled_items": len(item_to_labels),
            "num_communities": len(communities),
        },
        "communities": communities,
    }

    with out_path.open("w") as f:
        json.dump(payload, f, indent=2)

    print(out_path)
    print(json.dumps(payload["meta"], indent=2))


if __name__ == "__main__":
    main()
