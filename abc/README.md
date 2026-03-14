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
