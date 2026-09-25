# Sector spatial lemma

Sector polygons are planar rings of `x` `y` points in the same coordinate space as `fix_points.json`. Point-in-polygon uses ray casting with inclusive boundary treatment: a point that lies on an edge counts as inside.

A `sector` kind NOTAM row carries its own polygon for the penetration test. A flight fix that lies inside that polygon contributes a `sector_penetration` closure whose `detail` equals the NOTAM `sector_id`.

Aggregation of `sealed_sectors` uses the same ray-cast test against the catalog sectors. Axis-aligned bounding-box shortcuts are insufficient for concave sectors such as L-shaped rings and will over-report closures.
