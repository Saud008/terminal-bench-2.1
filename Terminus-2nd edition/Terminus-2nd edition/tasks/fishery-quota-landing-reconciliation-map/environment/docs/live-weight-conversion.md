# Live-weight conversion

conversion_factors maps lexicon species keys to a live-weight multiplier applied to product_weight_kg. This calibration step converts processed catch weights to live-weight equivalents for quota accounting.

live_weight_kg = round(product_weight_kg * factor, 2)

Factors above 1.0 represent gutted or processed product that weighs less than live weight.

Example: factor 1.15 converts 1000.0 product kg to 1150.0 live kg.
