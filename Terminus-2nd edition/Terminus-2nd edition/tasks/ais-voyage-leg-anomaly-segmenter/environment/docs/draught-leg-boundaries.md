# Draught leg boundaries

Voyage leg segmentation splits a track when draught changes by at least AIS_DRAUGHT_DELTA_M (default 0.5 meters) compared to the draught at the current leg first kept point. Port transitions also split legs per voyage-leg-rules.md. Draught splits apply after speed suppression on atlas.
