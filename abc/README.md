![make](https://img.shields.io/badge/make-4.3-brightgreen.svg)
![C++](https://img.shields.io/badge/C++-11.4.0-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
# Efficient (alpha, beta)-core computation in bipartite graphs

## Graph format

A `.meta` file contains the number of edges and the number of nodes in each part. See `data/example.meta` a `.e` file contains all the edges. See `data/example.e`

```
data
├── example.e
├── example.meta
```

## Build index

To build index with BasicDecom: 

```shell
./abcore -BasicDecom path_to_graph (e.g. ./abcore -BasicDecom ../data/example)
```

To build index with ComShrDecom: 

```shell
./abcore -ComShrDecom path_to_graph (e.g. ./abcore -ComShrDecom ../data/example)
```

To build index with ParallelDecom: 

```shell
./abcore -ParallelDecom path_to_graph num_cores (e.g. ./abcore -ParallelDecom ../data/example 20)
```

## Querying

To query alpha beta core using BiCoreIndex: 

```shell
./abcore -Query path_to_graph alpha beta (e.g. ./abcore -Query ../data/example 2 3)
```

## Dynamic operations

To insert edge with BiCore-Index-Ins: 

```shell
./abcore -BiCore-Index-Ins path_to_graph vertex_1 vertex_2 (e.g. ./abcore -BiCore-Index-Ins ../data/example 3 6)
```

To remove edge with BiCore-Index-Rem: 

```shell
./abcore -BiCore-Index-Rem path_to_graph vertex_1 vertex_2 (e.g. ./abcore -BiCore-Index-Rem ../data/example 3 7)
```

To insert edge with BiCore-Index-Ins*: 

```shell
./abcore -BiCore-Index-Ins* path_to_graph vertex_1 vertex_2 (e.g. ./abcore -BiCore-Index-Ins* ../data/example 3 6)
```

To remove edge with BiCore-Index-Rem*: 

```shell
./abcore -BiCore-Index-Rem* path_to_graph vertex_1 vertex_2 (e.g. ./abcore -BiCore-Index-Rem* ../data/example 3 7)
```

To insert edge with ParallelIns: 

```shell
./abcore -ParallelIns path_to_graph vertex_1 vertex_2 num_cores (e.g. ./abcore -BiCore-Index-Ins* ../data/example 3 6 20)
```

To remove edge with ParallelRem: 

```shell
./abcore -ParallelRem path_to_graph vertex_1 vertex_2 num_cores (e.g. ./abcore -BiCore-Index-Rem* ../data/example 3 7 20)
```

## Collaborating with Codex via GitHub (WSL quick steps)

If you prefer a simpler checklist, follow exactly these commands in order.

### Step 0: Open WSL

In Windows PowerShell:

```shell
wsl
```

If WSL fails to start, enable **Virtual Machine Platform** and **Windows Subsystem for Linux**, then reboot Windows.

### Step 1: Go to your project

```shell
cd /path/to/similar_ab_core
pwd
```

`pwd` should print the project directory.

### Step 2: Verify Git branch

```shell
git status -sb
git branch --show-current
```

If you already have `work`, switch to it:

```shell
git checkout work
```

If `git checkout work` says the branch does not exist, create it from current branch:

```shell
git checkout -b work
```

### Step 3: Connect this repo to GitHub

```shell
git remote -v
```

- If no `origin` appears:

```shell
git remote add origin https://github.com/<your-username>/<your-repo>.git
```

- If `origin` exists but URL is wrong:

```shell
git remote set-url origin https://github.com/<your-username>/<your-repo>.git
```

Check again:

```shell
git remote -v
```

### Step 4: First push (one-time)

```shell
git push -u origin work
```

### Step 5: Daily workflow with Codex

Before asking Codex to code:

```shell
git checkout work
git pull
```

After Codex finishes and pushes new commits:

```shell
git pull
```

Now your local files and GitHub stay in sync through the same `work` branch.


### Copy-paste commands for this exact repository

Use these commands exactly (the URL is already filled in):

```shell
# 1) open WSL
wsl

# 2) go to your local project path (replace this path with yours)
cd /path/to/similar_ab_core

# 3) ensure you are on the collaboration branch
git checkout work

# if branch does not exist yet, create it:
git checkout -b work

# 4) connect the GitHub remote (first-time setup)
git remote add origin https://github.com/Patrickxrc/similar_ab_core.git

# if previous command says origin already exists, run this instead:
git remote set-url origin https://github.com/Patrickxrc/similar_ab_core.git

# 5) verify remote
git remote -v

# 6) push local branch once
git push -u origin work
```

After this setup, your normal daily sync is:

```shell
# before working with Codex
git checkout work
git pull

# after Codex pushes changes
git pull
```
