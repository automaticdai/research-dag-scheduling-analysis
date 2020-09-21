# DAG Scheduling Simulator

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

This is the simulator used in the conference paper *DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency* for RTSS 2020. 


## Introduction

Simulate DAG tasksets execution on multi-cores. This software package supports:

- plug-in scheduling policies
- plug-in response time analysis (RTA)
- trace execution logs
- use with the [!dag-gen-rnd](https://github.com/automaticdai/dag-gen-rnd) DAG task generator
- configurable scheduling and task parameters


Supported scheduling alogrithms:

- Non-preemptive with random ordering
- Non-preemptive with eligibility ordering (proposed)
- Dynamic ordering (highest Ci first)
- Static prioirity assignment proposed in Q. He, N. Guan, Z. Guoet al., “Intra-task priority assignment in real-time  scheduling  of  DAG  tasks  on  multi-cores,”IEEE  Transactions  onParallel and Distributed Systems, vol. 30, no. 10, pp. 2283–2295, 2019.


Support response time analysis (RTA):

- Classical 1/m bound
- The proposed (alpha, beta) analysis
- The proposed (alpha, beta) analysis with eligibility ordering


Suppored execution models:

- WCET
- Full-random: [1, WCET]
- Half-random: [WCET/2, WCET]
- Random-a,b: [a * WCET, b * WCET]


For random, two algorithms can be chosen from:

- Normal distributed
- Uniformed distributed

(*) Note the normal distributed model is thresholded by 3 delta.


## Instructions

Before run, install Python libraries using pip:

`> sudo python3 -m pip install -r "requirements.txt"`

Then, run the simulator with:

`> python3 src/main.py >> results/result.log`

and finally:

`> python3 src/analysis.py`

The results will be in the `results` folder.


## Known Issues

No known issues up-to-date.


## Citation

Please cite the following paper if you use this code in your work:

Shuai Zhao, Xiaotian Dai, Iain Bate, Alan Burns and Wanli Chang. *DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency*. The IEEE Real-Time Systems Symposium. 2020.


## License

MIT License
