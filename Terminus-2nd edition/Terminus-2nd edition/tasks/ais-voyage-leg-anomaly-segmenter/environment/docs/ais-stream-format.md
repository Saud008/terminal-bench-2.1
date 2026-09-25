# AIS stream format

Bundled and hidden inputs are JSONL: one JSON object per line with fields seq (integer file order), mmsi (integer), ts (RFC3339 UTC with Z suffix), lat and lon (decimal degrees), sog (speed over ground in knots), draught (meters), and station (base station id string).

Lines must parse in file order. ts converts to ts_epoch as whole UTC seconds since Unix epoch; fractional seconds truncate toward zero. Invalid JSON or missing required fields fail feed with exit code 2.
