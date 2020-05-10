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


Supported scheduling alogrithm:

- Non-preemptive random
- Non-preemptive with eligibility ordering
- Preemptive workload distribution model

Suppored execution models:

- WCET
- Full random
- Half random

For random, two random algorithms can be selected:

- Normal distributed
- Uniformed distributed

(*) Note the normal distributed model is thresholded by 3 delta.


## Install & Run

Before run, install Python libraries using:

`> python3 -m pip install -r "requirements.txt"`

Then, run the simulator with:

`> python3 src/main.py`


## License

MIT License
