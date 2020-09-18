# DAG Scheduling Simulator

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

This is the simulator used in the work "DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency". 


## Introduction

Simulate DAG tasksets execution on multi-cores. This software package supports:

- plug-in scheduling policies
- plug-in response time analysis (RTA)
- trace execution logs
- use with rnd-dag-gen task generator
- configurable scheduling and task parameters


Supported scheduling alogrithms:

- Non-preemptive with random ordering
- Non-preemptive with eligibility ordering
- Dynamic C_high first 


Support response time analysis:

- classical 1/m bound
- (alpha, beta) analysis
- (alpha, beta) analysis with eligibility ordering


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

Before run, install Python libraries using:

`> python3 -m pip install -r "requirements.txt"`

Then, run the simulator with:

`> python3 src/main.py >> results/result.log`

and finally:

`> python3 src/analysis.py`

The results will be in the `results` folder.


## Known Issues

n/a


## Citation

Shuai Zhao, Xiaotian Dai, Iain Bate, Alan Burns, Wanli Chang. "DAG Scheduling and Analysis on Multiprocessor Systems: Exploitation of Parallelism and Dependency". The IEEE Real-Time Systems Symposium. 2020.

Please cite the above work if you use this code in your work.


## License

MIT License
