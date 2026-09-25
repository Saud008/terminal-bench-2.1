# CIP scheduling context

Seawater reverse-osmosis trains schedule chemical-in-place cleaning when normalized differential pressure slope exceeds plant-specific fouling ladders. Membrane element batches carry parent lineage so replacement modules inherit calibration baselines until a new batch window opens. Cleaning events reset pressure baselines only on the event hour, not on subsequent hours, so post-CIP recovery windows stay distinct from pre-cleaning fouling trends.

Operators compare brine-side pressure head loss against feed salinity drift because temperature and flow swings otherwise mask true fouling acceleration. Hold-last salinity bridging during sensor dropout prevents interpolated brine spikes from collapsing NDP scores, while pressure and flow gaps may still linearly interpolate when neighbors exist.

Pytest anti-hardcoding varies membrane batch labels, cleaning calendar dates, and sensor unit strings across bundled and hidden RO train fixtures so agents cannot memorize static chronicle digests.
