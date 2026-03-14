import tempfile
import subprocess
import os
import re
import time

path = "./proj_optim/sim_sub_tree"
for name in os.listdir(path):
    if '0.80.txt' not in name or 'bin' in name: continue
    # read graph
    graph_edge = set()
    start = time.time()
    with open(f'./proj_optim/data/{name.replace("result_", "").replace("_0.80.txt", "")}') as f:
        for line in f:
            if "%" in line: continue
            line = tuple(line.replace("\n", "").split())
            if len(line) > 2: continue

            graph_edge.add(line)
    # print(graph_edge)

    full_path = os.path.join(path, name)

    with open (full_path) as f:
        time_build = 0.0
        count = 0
        single_count = 0
        no_biclique_count = 0
        large_count = 0
        for line in f:
            count += 1
            line = line.replace('\n', '')
            line_re = re.compile(r"\{\s*([0-9\s]+)\s*\}\s*\|\s*\{\s*([0-9\s]+)\s*\}")
            m = line_re.match(line)
            left, right = m.groups()[0], m.groups()[1]
            left, right = left.split(), right.split()
            if len(left) == 1 or len(right) == 1: 
                single_count += 1
                continue
            
            sim_bi_graph = list()
            vl_cnt, vr_cnt = len(left), len(right)
            for u in left:
                for v in right:
                    if ((u, v)) in graph_edge:
                        sim_bi_graph.append((u, v))
                    if ((v, u)) in graph_edge:
                        sim_bi_graph.append((v, u))
            # print(sim_bi_graph)
            e_cnt = len(sim_bi_graph)
            if vl_cnt * vr_cnt > e_cnt:
                no_biclique_count += 1
            if vl_cnt >= 6 and vr_cnt >= 6:
                large_count += 1

            graph_dat = ""
            sim_bi_graph.sort(key=lambda x:(x[0], x[1]))

            left_ids = sorted(set(u for u, v in sim_bi_graph))
            right_ids = sorted(set(v for u, v in sim_bi_graph))

            left_map = {id_: idx for idx, id_ in enumerate(left_ids)}
            right_map = {id_: idx for idx, id_ in enumerate(right_ids)}

            mapped = [(left_map[u], right_map[v]) for u, v in sim_bi_graph]

            for e in mapped:
                graph_dat += f"{e[0]} {e[1]}\n"

            meta_dat = f"{vl_cnt}\n{vr_cnt}\n{e_cnt}\n"

            with open ("temp_data/graph.e", 'w') as f:
                f.write(graph_dat)
            with open ("temp_data/graph.meta", 'w') as f:
                f.write(meta_dat)

            result = subprocess.run(["./abcore", "-ComShrDecom", "temp_data/"], capture_output=True, text=True)
            result_out = result.stdout.split('\n')[-2].split(' ')[-1]
            # print(result_out)
            time_build += float(result_out)
        print(f"{name}: {time.time() - start:.03f}s, build time: {time_build:.03f}s, count: {count}, single count: {single_count}, ratio: {(single_count / count * 100):.03f}, no_biclique_count: {no_biclique_count}, large_count: {large_count}")

