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
- The proposed (alpha, beta) analysis with eligibility ordering


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

## Folder Organization

- `src/`: contains all source code in .py.
- `data/`: contains all the input data (from the DAG generator).
- `results/`: save all the intermediate raw results.
- `outputs/`: save all the produced diagrams.
- `requirements.txt`: Python libraries that are required.
- `README.md`: the repository readme document (this file).


## Known Issues

No known issues up-to-date.


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
