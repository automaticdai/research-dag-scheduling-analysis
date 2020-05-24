# DAG Scheduling Simulator

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

Simulate DAG tasksets execution on multi-cores. This package supports:

- plug-in schedulers
- analysis
- trace execution logs
- use with rnd-dag-gen task generator
- configurable scheduling and task parameters


Supported scheduling alogrithms:

- Non-preemptive random
- Non-preemptive with eligibility ordering
- (Todo) Preemptive Fixed-priority Scheduling 
- (Todo) Preemptive workload distribution model


Suppored execution models:

- WCET
- Full-random: [1, WCET]
- Half-random: [WCET/2, WCET]
- Random-a,b: [a * WCET, b * WCET]

For random, two algorithms can be chosen from:

- Normal distributed
- (Todo) Uniformed distributed

(*) Note the normal distributed model is thresholded by 3 delta.


## Install & Run

Before run, install Python libraries using:

`> python3 -m pip install -r "requirements.txt"`

Then, run the simulator with:

`> python3 src/main.py >> results/result.log`

and finally:

`> python3 src/analysis.py`

The results will be in the `results` folder.


## Known Issues

n/a


## License

MIT License
