import json
import time
import networkx as nx
import sys

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


with open (f"{graph_name}cpp_nei_VL_{similarity}.json") as f:
    L_nei = json.load(f)
with open (f"{graph_name}cpp_nei_VR_{similarity}.json") as f:
    R_nei = json.load(f)

G = nx.Graph()
nx.read_edgelist(graph_name, create_using=G)

possible_comb = []

# L_side_comb = []
# R_side_comb = []

def enumerate_comb(candidate_L: list, candidate_R: list, L_status: bool, curr_base_v: str, curr_nei_L: list, curr_nei_R: list, R_nei_count: dict, all_nei: dict):

    curr_nei = []
    candidate = []

    curr_nei = curr_nei_L if L_status else curr_nei_R
    candidate = candidate_L if L_status else candidate_R

    # print(L_status, candidate_L, candidate_R)

    # if L side candidate cannot be append, or one side 
    
    # if after adding a vertex to L side, then one vertex in R side has greater b, then stop
    if L_status and (b > 0 and b+1 in R_nei_count.values()):
        return
    
    # if after adding a vertex to L side, no vertex can be added, then a combination has formed
    elif L_status and not curr_nei:
        print(candidate_L, candidate_R)
        possible_comb.append([candidate_L.copy(), candidate_R.copy()])
        return
    
    # if after adding a vertex to R side, no vertex can be added or left vertex has reached a, then add vertex to left side
    elif not L_status and (not curr_nei or (a > 0 and len(candidate_R) == a)):

        all_R_nei_comb = set()
        for e in candidate:
            for e_nei in G.neighbors(e):
                all_R_nei_comb.add(e_nei)

        curr_nei_L_new = sorted([e for e in curr_nei_L if e in all_R_nei_comb], key=lambda x: int(x))

        R_nei_count = {e: 1 for e in candidate}

        enumerate_comb(candidate_L, candidate, True, curr_base_v, curr_nei_L_new, curr_nei_R, R_nei_count, all_nei)

    else:

        for v in curr_nei:
            # id is smaller than current v, then put to prev nei
            # if int(v) <= int(curr_base_v): 
            if candidate and int(v) <= int(candidate[-1]): 
                # prev_nei.append(v)
                continue
            
            # check if the added v is all similar to v in candidate
            candidate.append(v)
            curr_nei_new = []
            if v in all_nei:
                curr_nei_new = [e for e in curr_nei if e in all_nei[v]]


            if L_status:
                # if left status, add count of neighbour of right vertex

                for e in list(G.neighbors(v)):
                    if e in R_nei_count:
                        R_nei_count[e] += 1

                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_new, curr_nei_R, R_nei_count, all_nei)

                for e in list(G.neighbors(v)):
                    if e in R_nei_count:
                        R_nei_count[e] -= 1

            else:
                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_L, curr_nei_new, R_nei_count, all_nei)
            candidate.pop()
    

start_time = time.time()
# first enumerate all possible L-side
for v in L_nei:
    # print(v)
    v_simnei = L_nei[v]
    v_nei = list(G.neighbors(v))
    enumerate_comb([v], [], False, v, v_simnei, v_nei, dict(), {**L_nei, **R_nei})
end_time = time.time()

for e in possible_comb:
    print(e)
print(end_time - start_time)




