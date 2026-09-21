# Scenarios

One scenario, `BASE`: the base year as acquired, declared in `../overlays/scenarios/BASE.json`.
The assembled run inputs (`scenarios/matsim/BASE/`, one day type `WEEKDAY`) are written once by
`python cities/mumbai/build/build_baseline_run_inputs.py` (decision 9.204, #238) and read by the
framework's harness: `python run.py --scenario BASE --day WEEKDAY --run-config <overlay>`.
