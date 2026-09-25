# Route segment binding

Spatial correlation binds each event to the segment where start_m <= distance_m < end_m.
Segment attribution closure requires every bound event to fall inside exactly one route interval.
Attribute connector pair loss at segment boundaries using connector_start on the left segment and connector_end on the right segment only once per junction.
