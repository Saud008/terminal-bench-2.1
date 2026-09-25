# Trend classification ladder

Maintain an NDP series in hour_index order. After each reading, classify using slope from first to last NDP in the series:

  slope = (last_ndp - first_ndp) / (count - 1)

stable when slope <= 0.01
accelerating when slope <= 0.05
critical otherwise
