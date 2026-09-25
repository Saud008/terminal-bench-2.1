# Sensor calibration contract

Corrected peak ground vibration from each seismograph reading:

  corrected_ppv = (raw_ppv_mm_s - zero_offset_mm_s) * gain_multiplier

Apply per sensor_id from the survey sensor table. The atlas row attenuated_ppv_mm_s field stores max(corrected_ppv, attenuated_ppv) after both values are computed.
