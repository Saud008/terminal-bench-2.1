# Engineering problem contract

This task builds a seawater reverse-osmosis fouling trend profiler, not a kiln energy balance or generic ETL pipeline. rotrace converts brine-side pressure head loss, feed salinity drift, and permeate flow swings into ranked membrane fouling chronicles for CIP scheduling.

Correct behavior requires flow-temperature NDP normalization with T_ref over T exponent, membrane batch lineage inheritance along parent_batch_id chains, inclusive batch hour windows, salinity calibration subtract, cleaning baseline reset exactly on event hour, hold-last salinity dropout bridging with linear pressure and flow bridging, trend slope classification with count minus one denominator, batch_lineage_digest over sorted batch pairs, and chronicle_digest tied to summary counters plus sorted ndp_values.

Verifier pytest compares CLI output against an independent Python contract in tests/brine_ndp_contract.py. Anti-hardcoding probes randomize membrane labels, cleaning dates, and sensor units across bundled and hidden RO train fixtures.
