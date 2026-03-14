#include <iostream>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <string>
#include <algorithm>
#include <ctime>
#include "json.hpp"

using json = nlohmann::json;
using namespace std;


unordered_map<string, vector<string>> graph;
unordered_map<string, vector<string>> L_nei;
unordered_map<string, vector<string>> R_nei;
unordered_map<string, vector<string>> all_nei;
vector<pair<vector<string>, vector<string>>> possible_comb;

int a = 0, b = 0;

void load_json(const string& filename, unordered_map<string, vector<string>>& container) {
    ifstream file(filename);
    if (!file) {
        cerr << "Error opening file: " << filename << endl;
        exit(EXIT_FAILURE);
    }
    json data;
    file >> data;
    for (auto& [key, value] : data.items()) {
        container[key] = value.get<vector<string>>();
    }
}


void enumerate_comb(vector<string> candidate_L, vector<string> candidate_R, bool L_status,
                    const string& curr_base_v, const vector<string>& curr_nei_L,
                    const vector<string>& curr_nei_R, unordered_map<string, int>& R_nei_count,
                    const unordered_map<string, vector<string>>& all_nei) {

    const vector<string>& curr_nei = L_status ? curr_nei_L : curr_nei_R;
    vector<string>& candidate = L_status ? candidate_L : candidate_R;

    // cout << "curr nei: [ ";
    // for (const auto &v: curr_nei) {
    //     cout << v << " ";
    // }
    // cout << "] ";
    // cout << "curr candidate: [ ";
    // for (const auto &v: candidate) {
    //     cout << v << " ";
    // }
    // cout << "]" << endl;

    if (L_status && b > 0 && count_if(R_nei_count.begin(), R_nei_count.end(),
                                       [&](const auto& p) { return p.second == b + 1; }) > 0) {
        return;
    }
    else if (L_status && curr_nei.empty()) {
        possible_comb.emplace_back(candidate_L, candidate_R);
        return;
    }
    else if (!L_status && (curr_nei.empty() || (a > 0 && candidate_R.size() == static_cast<size_t>(a)))) {
        unordered_set<string> all_R_nei_comb;
        for (const auto& e : candidate_R) {
            if (graph.find(e) != graph.end()) {
                for (const auto& neighbor : graph[e]) {
                    all_R_nei_comb.insert(neighbor);
                }
            }
        }

        vector<string> curr_nei_L_new;
        for (const auto& e : curr_nei_L) {
            if (all_R_nei_comb.count(e)) {
                curr_nei_L_new.push_back(e);
            }
        }
        sort(curr_nei_L_new.begin(), curr_nei_L_new.end(), [](const string& a, const string& b) {
            return stoi(a) < stoi(b);
        });

        unordered_map<string, int> new_R_nei_count;
        for (const auto& e : candidate_R) {
            new_R_nei_count[e] = 1;
        }

        enumerate_comb(candidate_L, candidate_R, true, curr_base_v, curr_nei_L_new, curr_nei_R,
                       new_R_nei_count, all_nei);
    } else {
        for (const auto& v : curr_nei) {
            if (!candidate.empty() && stoi(v) <= stoi(candidate.back())) continue;

            candidate.push_back(v);
            vector<string> curr_nei_new;
            if (all_nei.count(v)) {
                for (const auto& e : curr_nei) {
                    if (find(all_nei.at(v).begin(), all_nei.at(v).end(), e) != all_nei.at(v).end()) {
                        curr_nei_new.push_back(e);
                    }
                }
            }


            if (L_status) {
                for (const auto& neighbor : graph[v]) {
                    R_nei_count[neighbor]++;
                }

                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_new,
                               curr_nei_R, R_nei_count, all_nei);

                for (const auto& neighbor : graph[v]) {
                    R_nei_count[neighbor]--;
                }
            } else {
                enumerate_comb(candidate_L, candidate_R, L_status, curr_base_v, curr_nei_L,
                               curr_nei_new, R_nei_count, all_nei);
            }
            candidate.pop_back();
        }
    }
}

int main(int argc, char* argv[]) {
    string graph_name, similarity;
    cout << "input graphname: ";
    cin >> graph_name;
    cout << "input similarity: ";
    cin >> similarity;

    if (argc > 1 && string(argv[1]) == "-d") {
        cout << "input alpha: ";
        cin >> a;
        cout << "input beta: ";
        cin >> b;
    }

    while (similarity.size() < 8) {
        similarity += '0';
    }

    string L_filename = graph_name + "cpp_nei_VL_" + similarity + ".json";
    string R_filename = graph_name + "cpp_nei_VR_" + similarity + ".json";
    
    load_json(L_filename, L_nei);
    load_json(R_filename, R_nei);

    cout << "load json ok" << endl;

    ifstream graph_file(graph_name);
    if (!graph_file) {
        cerr << "Error opening graph file: " << graph_name << endl;
        return EXIT_FAILURE;
    }

    string u, v;
    while (graph_file >> u >> v) {
        graph[u].push_back(v);
        graph[v].push_back(u);
    }

    cout << "load graph ok" << endl;

    all_nei.insert(L_nei.begin(), L_nei.end());
    all_nei.insert(R_nei.begin(), R_nei.end());

    clock_t start_time = clock();

    vector<string> sorted_L_nei_keys;

    for (const auto& pair : L_nei) {
        sorted_L_nei_keys.push_back(pair.first);
    }

    sort(sorted_L_nei_keys.begin(), sorted_L_nei_keys.end(), [](const string& a, const string& b) {
        return stoi(a) < stoi(b);
    });

    for (const auto& v : sorted_L_nei_keys) {
        cout << v << endl;
        vector<string> v_simnei = L_nei[v];
        vector<string> v_nei;
        if (graph.find(v) != graph.end()) {
            v_nei = graph[v];
        }
        
        unordered_map<string, int> R_nei_count;
        enumerate_comb({v}, {}, false, v, v_simnei, v_nei, R_nei_count, all_nei);
    }

    clock_t end_time = clock();
    
    for (const auto& comb : possible_comb) {
        cout << "[ ";
        for (const auto& l : comb.first) cout << l << " ";
        cout << "] - [ ";
        for (const auto& r : comb.second) cout << r << " ";
        cout << "]\n";
    }

    cout << "Time taken: " << double(end_time - start_time) / CLOCKS_PER_SEC << " seconds\n";
    
    return 0;
}