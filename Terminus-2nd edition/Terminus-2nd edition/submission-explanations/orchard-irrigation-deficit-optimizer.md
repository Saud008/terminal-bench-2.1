# Submission explanations — orchard-irrigation-deficit-optimizer

**Task folder:** tasks/orchard-irrigation-deficit-optimizer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a full agronomy pipeline where probe calibration, unit conversion, crop-stage coefficients, ET forecasts, quota carryover, and pump ceilings all change the same schedule. Fixing only probe math still leaves deficit scores wrong because ET demand must add to the moisture gap. Quota carryover and pump caps interact so a field that looks highest priority may receive zero liters once capacity is exhausted. Hidden scenarios use unfamiliar field aliases and mixed probe weights so threshold shortcuts fail.

## Solution Explanation

The oracle patches seven Rust modules that calibrate probes, convert depth units, look up Kc by stage, blend probes with weights, score deficits with ET demand, roll quota forward, and cap pump output per window. After patching, cargo rebuild installs irrctl and the export stage reads the staging ledger to emit sorted assignments and witness rows matching the independent Python reference planner.

## Verification Explanation

Pytest runs irrctl through subprocess after rebuilding the binary in test.sh. Bundled orchard scenarios cover offset traps, Kc indexing, weighted blends, quota carry, and pump limits. Two hidden tests load randomized field ids from verifier fixture roots and compare assignments and quota ledgers to irrctl_oracle.py reference math with numeric tolerance on liters and deficit millimeters.
