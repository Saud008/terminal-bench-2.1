# Sensor dropout bridge

Before NDP computation, bridge readings sorted by hour_index.

Salinity dropout (sensor_flags contains salinity_dropout): hold-last — copy salinity_ppt from the previous hour row; do not linearly interpolate salinity.

Pressure dropout: linearly interpolate pressure_bar between previous and next valid hours.

Flow dropout: linearly interpolate flow_m3h between previous and next valid hours.
