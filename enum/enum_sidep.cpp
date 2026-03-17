#include <iostream>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <string>
#include <algorithm>
#include <ctime>
#include <chrono>
#include <thread>
#include <mutex>
#include <queue>
#include <condition_variable>
#include "json.hpp"

int limit = 4;

using json = nlohmann::json;
using namespace std;

enum class SimMode { Both, LeftOnly, RightOnly };
SimMode sim_mode = SimMode::Both;

bool should_apply_similarity(bool selecting_left_vertices) {
    if (sim_mode == SimMode::Both) return true;
    if (sim_mode == SimMode::LeftOnly) return selecting_left_vertices;
    return !selecting_left_vertices;
}

unordered_map<string, vector<string>> graph;
unordered_map<string, vector<string>> L_nei;
unordered_map<string, vector<string>> R_nei;
unordered_map<string, vector<string>> all_nei;
vector<pair<vector<string>, vector<string>>> possible_comb;
mutex comb_mutex;
mutex cout_mutex;

mutex queue_mutex;
condition_variable cv;
queue<string> task_queue;
bool stop_workers = false;
int active_workers = 0;
mutex active_workers_mutex;


int a = 0, b = 0;
const int THREAD_COUNT = 30;

void safe_print(const string& message, bool endl_status) {
    lock_guard<mutex> lock(cout_mutex);
    cout << message;
    if (endl_status) cout << endl;
}

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

    // string print_text = "candidate: [ ";
    // for (const auto &v: candidate_L) {
    //     print_text += (v + " ");
    // }
    // print_text += "]";
    // safe_print(print_text, true);

    if (L_status && b > 0 && count_if(R_nei_count.begin(), R_nei_count.end(),
                                      [&](const auto& p) { return p.second == b + 1; }) > 0) {
        return;
    } 
    else if (L_status && curr_nei.empty()) {
        lock_guard<mutex> lock(comb_mutex);
        possible_comb.emplace_back(candidate_L, candidate_R);
        // cout << "candidate_L: [ ";
        // for (const auto &v: candidate_L) {
        //     cout << v << " ";
        // }
        // cout << "] ";
        // cout << "candidate_R: [ ";
        // for (const auto &v: candidate_R) {
        //     cout << v << " ";
        // }
        // cout << "]" << endl;
        // return;
    } 
    else if (!L_status && (curr_nei.empty() || (a > 0 && candidate_R.size() == static_cast<size_t>(a)))) {

        if (limit != 0 && candidate_R.size() < limit) return;

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
            if (should_apply_similarity(L_status) && all_nei.count(v)) {
                for (const auto& e : curr_nei) {
                    if (find(all_nei.at(v).begin(), all_nei.at(v).end(), e) != all_nei.at(v).end()) {
                        curr_nei_new.push_back(e);
                    }
                }
            } else {
                curr_nei_new = curr_nei;
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

void worker_thread() {
    while (true) {
        string v;
        {
            unique_lock<mutex> lock(queue_mutex);
            cv.wait(lock, [] { return !task_queue.empty() || stop_workers; });

            if (stop_workers && task_queue.empty()) {
                return;
            }

            v = task_queue.front();
            task_queue.pop();
        }

        {
            lock_guard<mutex> lock(active_workers_mutex);
            active_workers++;
        }

        vector<string> v_simnei = L_nei[v];
        vector<string> v_nei;
        if (graph.find(v) != graph.end()) {
            v_nei = graph[v];
        }

        unordered_map<string, int> R_nei_count;
        
        enumerate_comb({v}, {}, false, v, v_simnei, v_nei, R_nei_count, all_nei);
        cout << v << endl;

        {
            lock_guard<mutex> lock(active_workers_mutex);
            active_workers--;
        }

        cv.notify_all();
    }
}

int main(int argc, char* argv[]) {
    string graph_name, similarity;
    cout << "input graphname: ";
    cin >> graph_name;
    cout << "input similarity: ";
    cin >> similarity;

    string sim_mode_input;
    cout << "input sim mode (both/sim_left/sim_right): ";
    cin >> sim_mode_input;
    if (sim_mode_input == "sim_left") sim_mode = SimMode::LeftOnly;
    else if (sim_mode_input == "sim_right") sim_mode = SimMode::RightOnly;
    else sim_mode = SimMode::Both;

    if (argc > 1 && string(argv[1]) == "-d") {
        cout << "input alpha: ";
        cin >> a;
        cout << "input beta: ";
        cin >> b;
    }

    while (similarity.size() < 8) {
        similarity += '0';
    }

    string L_filename, R_filename;
    if (sim_mode == SimMode::LeftOnly) {
        L_filename = graph_name + "cpp_nei_sim_left_VL" + similarity + ".json";
        R_filename = graph_name + "cpp_nei_sim_left_VR" + similarity + ".json";
    } else if (sim_mode == SimMode::RightOnly) {
        L_filename = graph_name + "cpp_nei_sim_right_VL" + similarity + ".json";
        R_filename = graph_name + "cpp_nei_sim_right_VR" + similarity + ".json";
    } else {
        L_filename = graph_name + "cpp_nei_VL_" + similarity + ".json";
        R_filename = graph_name + "cpp_nei_VR_" + similarity + ".json";
    }

    load_json(L_filename, L_nei);
    load_json(R_filename, R_nei);

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

    all_nei.insert(L_nei.begin(), L_nei.end());
    all_nei.insert(R_nei.begin(), R_nei.end());

    vector<string> sorted_L_nei_keys;
    for (const auto& pair : L_nei) {
        sorted_L_nei_keys.push_back(pair.first);
    }
    sort(sorted_L_nei_keys.begin(), sorted_L_nei_keys.end(), [](const string& a, const string& b) {
        return stoi(a) < stoi(b);
    });

    auto start_time = std::chrono::high_resolution_clock::now();

    vector<thread> threads;
    for (int i = 0; i < THREAD_COUNT; ++i) {
        threads.emplace_back(worker_thread);
    }

    {
        lock_guard<mutex> lock(queue_mutex);
        for (const auto& v : sorted_L_nei_keys) {
            task_queue.push(v);
        }
    }
    cv.notify_all();

    while (true) {
        lock_guard<mutex> lock(active_workers_mutex);
        if (task_queue.empty() && active_workers == 0) {
            break;
        }
    }

    {
        lock_guard<mutex> lock(queue_mutex);
        stop_workers = true;
    }
    cv.notify_all();

    for (auto& th : threads) {
        th.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_time = end_time - start_time;

    // cout << "Time taken: " << double(end_time - start_time) / CLOCKS_PER_SEC << " seconds\n";

    cout << "Time taken: " << elapsed_time.count() << " seconds" << endl;


    

    std::ofstream outfile(graph_name + "_" + similarity + "_" + to_string(a) + "_" + to_string(b) + "_enum_sidep_" + to_string(limit) + ".txt");
    std::string content = "";
    
    for (const auto& comb : possible_comb) {
        content += "[ ";
        for (const auto& l : comb.first) content += (l + " ");
        content += "] - [ ";
        for (const auto& r : comb.second) content += (r + " ");
        content += "]\n";
    }

    outfile << content;

    outfile.close();

    return 0;
}