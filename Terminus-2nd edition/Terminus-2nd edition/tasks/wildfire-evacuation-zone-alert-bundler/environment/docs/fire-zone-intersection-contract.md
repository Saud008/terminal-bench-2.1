# Fire zone intersection contract

A zone is fire-affected when its polygon intersects any fire perimeter polygon. Intersection requires ray-cast point-in-polygon tests for vertices inside the opposite polygon or segment intersection between any edge pairs. Bounding-box overlap alone is not sufficient for concave zones.
