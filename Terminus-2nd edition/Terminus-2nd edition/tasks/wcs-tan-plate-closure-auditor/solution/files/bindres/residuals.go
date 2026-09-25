package bindres

import (
	"math"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/terminus/platclosectl/internal/epochnudge"
	"github.com/terminus/platclosectl/internal/model"
	"github.com/terminus/platclosectl/internal/qmask"
	"github.com/terminus/platclosectl/internal/tanproj"
)

func Bind(s model.Scenario, p model.Plate) []model.Residual {
	tol := s.MatchArcsec
	if x := os.Getenv("TB3_MATCH_ARCSEC"); x != "" {
		if v, err := strconv.ParseFloat(x, 64); err == nil {
			tol = v
		}
	}
	out := make([]model.Residual, 0, len(s.Stars))
	for _, star := range s.Stars {
		if qmask.Exclude(star.DetMask, star.CatMask) {
			continue
		}
		predRA, predDec := tanproj.Project(p, star.X, star.Y)
		targetRA := epochnudge.RA(star.RADeg, star.Epoch, p.Epoch)
		dra := (predRA - targetRA) * 3600.0
		ddec := (predDec - star.DecDeg) * 3600.0
		sep := math.Hypot(dra, ddec)
		if sep <= tol {
			out = append(out, model.Residual{
				StarID:   star.StarID,
				DeltaRA:  dra,
				DeltaDec: ddec,
				Sep:      sep,
			})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].StarID < out[j].StarID })
	return out
}

func Matrix(s model.Scenario, rows []model.Residual) string {
	var b strings.Builder
	b.WriteString(`{"type":"residual-matrix","scenario_id":"`)
	b.WriteString(s.ScenarioID)
	b.WriteString("\"}\n")
	for _, row := range rows {
		b.WriteString(`{"star_id":"`)
		b.WriteString(row.StarID)
		b.WriteString(`","delta_ra_arcsec":`)
		b.WriteString(strconv.FormatFloat(row.DeltaRA, 'f', 6, 64))
		b.WriteString(`,"delta_dec_arcsec":`)
		b.WriteString(strconv.FormatFloat(row.DeltaDec, 'f', 6, 64))
		b.WriteString(`,"sep_arcsec":`)
		b.WriteString(strconv.FormatFloat(row.Sep, 'f', 6, 64))
		b.WriteString("}\n")
	}
	return b.String()
}
