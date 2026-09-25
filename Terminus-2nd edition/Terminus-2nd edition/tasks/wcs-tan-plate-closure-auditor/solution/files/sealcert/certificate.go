package sealcert

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"sort"

	"github.com/terminus/platclosectl/internal/model"
)

func round6(v float64) float64 {
	return math.Floor(v*1e6+0.5) / 1e6
}

func Certificate(scenarioID string, rows []model.Residual) ([]byte, error) {
	if len(rows) == 0 {
		return nil, fmt.Errorf("no active residuals")
	}
	var sumRA, sumDec float64
	ids := make([]string, 0, len(rows))
	for _, row := range rows {
		sumRA += row.DeltaRA * row.DeltaRA
		sumDec += row.DeltaDec * row.DeltaDec
		ids = append(ids, row.StarID)
	}
	sort.Strings(ids)
	ra := round6(math.Sqrt(sumRA / float64(len(rows))))
	dec := round6(math.Sqrt(sumDec / float64(len(rows))))
	digestPayload := fmt.Sprintf(
		`{"scenario_id":%q,"active_count":%d,"star_ids":%s,"rms_ra_arcsec":%.6f,"rms_dec_arcsec":%.6f}`,
		scenarioID, len(ids), mustJSON(ids), ra, dec,
	)
	sum := sha256.Sum256([]byte(digestPayload))
	class := "loose"
	if ra < 0.35 && dec < 0.35 {
		class = "tight"
	}
	return json.Marshal(map[string]interface{}{
		"scenario_id":    scenarioID,
		"matched_count":  len(rows),
		"active_count":   len(ids),
		"rms_ra_arcsec":  ra,
		"rms_dec_arcsec": dec,
		"closure_class":  class,
		"stars":          ids,
		"closure_digest": hex.EncodeToString(sum[:]),
	})
}

func mustJSON(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
