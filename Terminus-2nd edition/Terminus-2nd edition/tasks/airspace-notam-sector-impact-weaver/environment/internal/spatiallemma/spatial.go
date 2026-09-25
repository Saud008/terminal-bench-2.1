package spatiallemma

import "github.com/terminus/airclos/internal/labtypes"

// PointInside tests whether p lies within poly per sector-spatial-lemma.md.
func PointInside(p labtypes.Point, poly []labtypes.Point) bool {
	if len(poly) < 3 {
		return false
	}
	minX, maxX := poly[0].X, poly[0].X
	minY, maxY := poly[0].Y, poly[0].Y
	for _, v := range poly[1:] {
		if v.X < minX {
			minX = v.X
		}
		if v.X > maxX {
			maxX = v.X
		}
		if v.Y < minY {
			minY = v.Y
		}
		if v.Y > maxY {
			maxY = v.Y
		}
	}
	return p.X >= minX && p.X <= maxX && p.Y >= minY && p.Y <= maxY
}

func SectorForPoint(p labtypes.Point, sectors []labtypes.Sector) []string {
	var hits []string
	for _, s := range sectors {
		if PointInside(p, s.Polygon) {
			hits = append(hits, s.SectorID)
		}
	}
	return hits
}
