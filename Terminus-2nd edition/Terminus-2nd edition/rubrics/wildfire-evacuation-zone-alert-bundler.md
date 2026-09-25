# Platform rubric — wildfire-evacuation-zone-alert-bundler

**Task folder:** tasks/wildfire-evacuation-zone-alert-bundler/

Agent implements ray-cast fire-zone intersection instead of bounding-box overlap, +3
Agent routes evacuees with BFS that skips closed road edges, +3
Agent decrements shelter remaining capacity on each assignment, +3
Agent orders alert bundles by numeric severity rank then zone_id, +3
Agent copies staging_digest from weave staging into seal export, +2
Agent reads staging ledger only during seal export, +2
Agent matches full alert bundle output to independent reference math, +3
Agent rebuilds evacbundle before pytest subprocess invocations, +2
Agent uses weather_stub decoy module on the export hot path, -3
Agent keeps bounding-box-only geometry checks for concave zones, -3
Agent traverses closed highway edges during shelter routing, -3
Agent sorts bundles by zone_id without severity precedence, -2
Agent omits staging_digest from sealed export JSON, -2
