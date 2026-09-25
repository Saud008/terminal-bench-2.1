# Pressure buffer schema

Path: /app/state/pressure-buffer/<run-id>.jsonl

First line JSON header with run_id and stage pressure. Each following line is a staged reading with hour_index, batch_id, pressure_bar, salinity_ppt, flow_m3h, temperature_c, sensor_flags, cal_offset_ppt. load-readings may override cal_offset_ppt from --cal-table or TB3_CAL_TABLE hour_index salinity_offset_ppt rows.
