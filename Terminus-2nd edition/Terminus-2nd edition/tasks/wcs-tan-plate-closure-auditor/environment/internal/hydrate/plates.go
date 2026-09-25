package hydrate

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/platclosectl/internal/model"
)

type wireStar struct {
	StarID  string  `json:"star_id"`
	X       float64 `json:"x_pixel"`
	Y       float64 `json:"y_pixel"`
	RADeg   float64 `json:"ra_deg"`
	DecDeg  float64 `json:"dec_deg"`
	Epoch   float64 `json:"epoch_year"`
	DetMask int     `json:"det_mask"`
	CatMask int     `json:"cat_mask"`
}

type wireScenario struct {
	ScenarioID  string     `json:"scenario_id"`
	HeaderCards []string   `json:"header_cards"`
	Stars       []wireStar `json:"stars"`
	MatchArcsec float64    `json:"match_arcsec"`
}

func Load(id string) (model.Scenario, error) {
	dir := os.Getenv("TB3_FIXTURE_DIR")
	if dir == "" {
		dir = "/app/fixtures/scenarios"
	}
	raw, err := os.ReadFile(filepath.Join(dir, id+".json"))
	if err != nil {
		return model.Scenario{}, err
	}
	var w wireScenario
	if err := json.Unmarshal(raw, &w); err != nil {
		return model.Scenario{}, err
	}
	out := model.Scenario{
		ScenarioID:  w.ScenarioID,
		HeaderCards: w.HeaderCards,
		MatchArcsec: w.MatchArcsec,
	}
	if out.MatchArcsec == 0 {
		out.MatchArcsec = 2.5
	}
	for _, star := range w.Stars {
		out.Stars = append(out.Stars, model.Star{
			StarID:  star.StarID,
			X:       star.X,
			Y:       star.Y,
			RADeg:   star.RADeg,
			DecDeg:  star.DecDeg,
			Epoch:   star.Epoch,
			DetMask: star.DetMask,
			CatMask: star.CatMask,
		})
	}
	return out, nil
}
