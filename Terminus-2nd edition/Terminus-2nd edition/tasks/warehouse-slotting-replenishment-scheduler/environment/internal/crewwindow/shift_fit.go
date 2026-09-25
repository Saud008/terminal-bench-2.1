package crewwindow

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/whslot/internal/replenledger"
	"github.com/terminus/whslot/internal/yardfeed"
)

func WorkerFits(wShiftStart, wShiftEnd, tStart, tEnd int) bool {
	if tStart < wShiftStart {
		return false
	}
	return tEnd < wShiftEnd
}

func Run() error {
	bundle, err := yardfeed.ReadActive()
	if err != nil {
		return err
	}
	db, err := replenledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	tasks, err := fetchTasks(db)
	if err != nil {
		return err
	}
	for _, t := range tasks {
		assigned := ""
		for _, w := range bundle.Workers {
			if WorkerFits(w.ShiftStart, w.ShiftEnd, t.Start, t.End) {
				assigned = w.WorkerID
				break
			}
		}
		if assigned == "" {
			return errNoWorker
		}
		if err := replenledger.BindWorker(db, t.Key, assigned); err != nil {
			return err
		}
	}
	raw, _ := json.Marshal(map[string]int{"wave_latch_pass": 1})
	if err := os.WriteFile("/app/state/wave-latch-pass.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return replenledger.SetMeta(db, "wave_latch_pass", "1")
}

var errNoWorker = os.ErrInvalid

type taskRow struct {
	Key   string
	Start int
	End   int
}

func fetchTasks(db *sql.DB) ([]taskRow, error) {
	rs, err := db.Query(`SELECT task_key,start_minute,end_minute FROM wave_tasks ORDER BY task_key`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []taskRow
	for rs.Next() {
		var r taskRow
		if err := rs.Scan(&r.Key, &r.Start, &r.End); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rs.Err()
}
