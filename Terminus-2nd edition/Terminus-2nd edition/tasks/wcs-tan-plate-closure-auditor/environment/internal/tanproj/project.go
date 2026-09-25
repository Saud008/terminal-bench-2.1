package tanproj

import "github.com/terminus/platclosectl/internal/model"

func Project(p model.Plate, x, y float64) (float64, float64) {
	xi := x - p.CRPIX[0] + 1.0
	eta := y - p.CRPIX[1] + 1.0
	ra := p.CRVAL[0] + p.CD[0][0]*xi + p.CD[0][1]*eta
	dec := p.CRVAL[1] + p.CD[1][0]*xi + p.CD[1][1]*eta
	return ra, dec
}
