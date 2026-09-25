# Flow-temperature NDP normalization

NDP for each reading after cleaning baseline selection:

  ndp = (pressure_bar - p_base) * (T_ref / temperature_c) ** alpha * (Q_ref / flow_m3h) ** beta * (1 + salinity_ppt / 1000)

Use batch-resolved alpha, beta, T_ref, and Q_ref from membrane batch lineage. p_base comes from cleaning reset window contract.
