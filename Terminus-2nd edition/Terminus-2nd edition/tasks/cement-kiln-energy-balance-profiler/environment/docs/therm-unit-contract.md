# Thermodynamic unit contract

Telemetry temp_raw uses unit C for Celsius or K for Kelvin. Normalize to Celsius before calibration: Celsius stays unchanged; Kelvin uses temp_c = temp_raw - 273.15.

Fuel energy converts with energy_mj = mass_kg * cv_kcal_kg * kcal_to_mj where kcal_to_mj comes from kilnbal.json (0.004184).
