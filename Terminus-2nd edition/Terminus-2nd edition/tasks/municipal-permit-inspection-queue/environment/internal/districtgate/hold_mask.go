package districtgate

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/mpiqctl/internal/permitstore"
	"github.com/terminus/mpiqctl/internal/zoninghold"
)

func ApplyHolds() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	mask, err := buildHoldMask(db)
	if err != nil {
		return err
	}
	raw, err := json.Marshal(mask)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/work/hold-mask.json", append(raw, '\n'), 0o644)
}

func buildHoldMask(db *sql.DB) (map[string]int, error) {
	rs, err := db.Query(`SELECT district_id, hold_rank, active FROM zoning_holds`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	mask := map[string]int{}
	for rs.Next() {
		var district string
		var rank, active int
		if err := rs.Scan(&district, &rank, &active); err != nil {
			return nil, err
		}
		hr := zoninghold.ActiveHoldRank(rank, active == 1)
		if hr == 0 {
			continue
		}
		cur := mask[district]
		if cur == 0 || hr < cur {
			mask[district] = hr
		}
	}
	return mask, rs.Err()
}

func DistrictHoldRank(mask map[string]int, district string) int {
	return mask[district]
}
