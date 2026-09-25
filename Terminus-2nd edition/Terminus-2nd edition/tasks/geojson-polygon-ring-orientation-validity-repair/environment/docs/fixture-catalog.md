# Fixture catalog

Files under `/app/fixtures/geojson/*.json`:

| File | Geometry | Intent |
|------|----------|--------|
| `exterior-cw.json` | Polygon | Exterior ring wound clockwise |
| `hole-wrong-wind.json` | Polygon | Hole wound CCW |
| `hole-outside-order.json` | Polygon | Hole ring listed first / wrong exterior |
| `duplicate-verts.json` | Polygon | Consecutive duplicate vertices |
| `double-close.json` | Polygon | Closing vertex duplicated in ring |
| `multi-two.json` | MultiPolygon | Two member polygons |
| `multi-hole-nest.json` | MultiPolygon | First member has a hole; second member is a simple polygon |
| `clean-square.json` | Polygon | Already valid square |
