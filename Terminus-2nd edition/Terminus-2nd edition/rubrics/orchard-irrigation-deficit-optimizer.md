# Platform rubric — orchard-irrigation-deficit-optimizer

**Task folder:** tasks/orchard-irrigation-deficit-optimizer/

Agent subtracts probe calibration offsets when blending volumetric water content, +3
Agent converts root-zone moisture gap to millimeters using depth times 100 scale, +3
Agent indexes crop-stage Kc curve without off-by-one stage shift, +2
Agent area-weights probe readings instead of arithmetic averaging, +3
Agent adds ET demand millimeters into deficit scoring not moisture gap alone, +3
Agent carries unused district quota cubic meters into the next window, +2
Agent enforces pump liters per slot ceiling during scheduling, +2
Agent sorts irrigation assignments by field_id then window_index ascending, +2
Agent matches irrigation plan output to independent numeric reference planner, +3
Agent averages probe offsets without applying per-probe weights, -3
Agent uses wrong depth divisor when converting volumetric fraction to millimeters, -3
Agent schedules irrigation ignoring max liters per hour pump limit, -3
Agent drops ET crop coefficient demand from deficit priority score, -2
