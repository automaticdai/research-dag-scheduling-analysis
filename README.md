# DAG Scheduling and Analysis on Multiprocessor Systems

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

## Introduction

Simulate DAG tasksets execution on multi-cores. This software package supports:

- plug-in scheduling policies
- plug-in response time analysis (RTA)
- trace execution logs
- use with the [dag-gen-rnd](https://github.com/automaticdai/dag-gen-rnd) DAG task generator
- configurable scheduling and task parameters


Supported scheduling algorithms:

- Non-preemptive with random ordering
- Non-preemptive with node-level execution ordering (proposed)
- Dynamic ordering (highest Ci first)
- Static priority assignment proposed in Q. He, N. Guan, Z. Guo et al., “Intra-task priority assignment in real-time  scheduling  of  DAG  tasks  on  multi-cores,”IEEE  Transactions  on Parallel and Distributed Systems, vol. 30, no. 10, pp. 2283–2295, 2019.


Support response time analysis (RTA):

- Classical 1/m bound
- The proposed (alpha, beta) analysis
- The proposed (alpha, beta) analysis with eligibility ordering (EO)


Supported execution models:

- WCET
- Full-random: [1, WCET]
- Half-random: [WCET/2, WCET]
- Random-a,b: [a * WCET, b * WCET]


For random, two distribution functions can be chosen from:

- Normal distribution
- Uniform distribution

(*) Note the normal distributed model is threshold by 3 delta.

## Instructions

Before run, install Python libraries using pip:

`> sudo python3 -m pip install -r "requirements.txt"`

Then, run the simulator with:

`> python3 src/main.py >> results/result.log`

and finally:

`> python3 src/analysis.py`

The results will be in the `results` folder.

**To reproduce the results in RTSS 2020** (notice there is a known issue; see below):

`> python3 src/rtss_ae.py`

## Folder Organization

- `data/`: contains all the input data (from the DAG generator).
- `src/`: contains all source code in .py.
  - `main.py`: the main file of the DAG simulator
  - `rta_alphabeta_new.py`: the proposed priority ordering and (alpha, beta) response time analysis
  - 
- `results/`: save all the intermediate raw results.
- `outputs/`: save all the produced diagrams.
- `requirements.txt`: Python libraries that are required.
- `README.md`: the repository readme document (this file).


## Known Issues

- (2021/04/27) As reported by the first author (Qingqiang He) of TPDS'2019. There is a bug on the recursion of  DAGs which causes the algorithm sometimes find sub-optimal longest paths. This bug should not affect major conclusions of the paper as both ours and He'2019 rely on this same buggy function routine. We have solved this issue in the latest release. However, if you are looking to reproduce the exactly results as in RTSS'2020, please checkout the version tagged with `rtss2020-ae` by using `git checkout rtss2020-ae`


## Citation

Please cite the following paper if you use this code in your work:

Shuai Zhao, Xiaotian Dai, Iain Bate, Alan Burns and Wanli Chang. *DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency*. The IEEE Real-Time Systems Symposium. 2020.


BibTex entry:

```text
@inproceedings{zhao2020dag,
  title={DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency},
  author={Zhao, Shuai and Dai, Xiaotian and Bate, Iain and Burns, Alan and Chang, Wanli},
  booktitle={IEEE Real-Time Systems Symposium},
  year={2020},
  organization={IEEE}
}
```

## License

MIT License