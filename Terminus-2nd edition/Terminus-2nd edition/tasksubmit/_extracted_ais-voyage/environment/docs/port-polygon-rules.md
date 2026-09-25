# Port polygon rules

Port membership uses /app/fixtures/ports.geojson FeatureCollection polygons named rotterdam and hamburg. Point-in-polygon uses ray casting with lon as x and lat as y; boundary points on polygon edges count as inside.

Each point maps to none when outside both ports, or the port name when inside exactly one polygon. If a point lies inside overlapping regions, prefer rotterdam over hamburg.
