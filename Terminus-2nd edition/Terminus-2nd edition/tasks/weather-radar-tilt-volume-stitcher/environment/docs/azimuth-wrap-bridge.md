# Azimuth wrap bridge

Ray azimuth_centideg values use hundredths of a degree on the circle 0 through 35999. Spatial azimuth bridging converts each ray to bridged_azimuth_centideg by adding 36000 to rays that follow a decrease in raw azimuth within the same tilt scan sequence.

azimuth_coverage_centideg equals max bridged minus min bridged across all gates in the stitch pass. A sequence 358.00, 359.00, 0.50 degrees must yield span 250 centideg not 35850.
