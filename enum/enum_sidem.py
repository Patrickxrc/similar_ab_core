import json
import time
import networkx as nx
import sys
import concurrent.futures
import multiprocessing
# from multiprocessing import current_process
# sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)


L_nei = dict()
R_nei = dict()

graph_name = input("input graphname: ")
similarity = input("input similarity: ")

a = 0
b = 0
if len(sys.argv) > 1 and sys.argv[1] == '-d':
    a = int(input("input alpha: "))
    b = int(input("input beta: "))

while len(similarity) < 8:
    similarity += '0'

with open(f"{graph_name}cpp_nei_VL_{similarity}.json") as f:
    L_nei = json.load(f)
with open(f"{graph_name}cpp_nei_VR_{similarity}.json") as f:
    R_nei = json.load(f)

G = nx.Graph()
nx.read_edgelist(graph_name, create_using=G)



def enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_L, curr_nei_R, R_nei_count, all_nei, local_comb):
    curr_nei = curr_nei_L if L_status else curr_nei_R
    candidate = candidate_L if L_status else candidate_R

    

    if L_status and (b > 0 and b + 1 in R_nei_count.values()):
        # print(candidate_L[:-1], candidate_R)
        # local_comb.append([candidate_L.copy()[:-1], candidate_R.copy()])
        return
    elif L_status and not curr_nei:
        # print(candidate_L, candidate_R)
        # print(f"[{current_process().name}] {candidate_L} {candidate_R}", flush=True)
        local_comb.append([candidate_L.copy(), candidate_R.copy()])
        return
    elif not L_status and (not curr_nei or (a > 0 and len(candidate_R) == a)):
        # test
        # if len(candidate) < 3: return
        # test end
        all_R_nei_comb = set()
        for e in candidate:
            for e_nei in G.neighbors(e):
                all_R_nei_comb.add(e_nei)

        curr_nei_L_new = sorted([e for e in curr_nei_L if e in all_R_nei_comb], key=lambda x: int(x))
        R_nei_count = {e: 1 for e in candidate}

        enumerate_comb(candidate_L, candidate, True, curr_base_v, curr_nei_L_new, curr_nei_R, R_nei_count, all_nei, local_comb)
    else:
        for v in curr_nei:
            if candidate and int(v) <= int(candidate[-1]):
                continue

            candidate.append(v)
            curr_nei_new = [e for e in curr_nei if e in all_nei.get(v, [])]

            if L_status:
                for e in G.neighbors(v):
                    if e in R_nei_count:
                        R_nei_count[e] += 1
                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_new, curr_nei_R, R_nei_count, all_nei, local_comb)
                for e in G.neighbors(v):
                    if e in R_nei_count:
                        R_nei_count[e] -= 1
            else:
                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_L, curr_nei_new, R_nei_count, all_nei, local_comb)

            candidate.pop()



def process_vertex(v, shared_possible_comb):
    print(v)
    v_simnei = L_nei[v]
    v_nei = list(G.neighbors(v))
    local_comb = []
    enumerate_comb([v], [], False, v, v_simnei, v_nei, dict(), {**L_nei, **R_nei}, local_comb)


    with shared_possible_comb.get_lock():
        shared_possible_comb.extend(local_comb)



if __name__ == "__main__":
    start_time = time.time()

    # num_workers = multiprocessing.cpu_count()
    num_workers = 30
    manager = multiprocessing.Manager()
    shared_possible_comb = manager.list()


    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_vertex, v, shared_possible_comb) for v in L_nei.keys()]
        concurrent.futures.wait(futures)

    end_time = time.time()


    for e in shared_possible_comb:
        print(e)
    print("Execution time:", end_time - start_time)