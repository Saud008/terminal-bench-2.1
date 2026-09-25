package export

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/harbor/tug-berth/internal/db"
	"github.com/harbor/tug-berth/internal/overlap"
	"github.com/harbor/tug-berth/internal/staging"
	"github.com/harbor/tug-berth/pkg/util"
)

type berthReport struct {
	BerthID                  string           `json:"berth_id"`
	ConcurrentOverlapMinutes int              `json:"concurrent_overlap_minutes"`
	TotalDwellMinutes        int              `json:"total_dwell_minutes"`
	Assignments              []assignmentView `json:"assignments"`
}

type assignmentView struct {
	VoyageID     string `json:"voyage_id"`
	MMSI         int64  `json:"mmsi"`
	ArrivalUTC   string `json:"arrival_utc"`
	DepartureUTC string `json:"departure_utc"`
}

type report struct {
	Berths        []berthReport `json:"berths"`
	ReplayStats   replayView    `json:"replay_stats"`
	StagingDigest string        `json:"staging_digest"`
}

type replayView struct {
	Accepted          int `json:"accepted"`
	DuplicateRejected int `json:"duplicate_rejected"`
}

func Run(args []string) error {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	dbPath := fs.String("db", "/app/state/berth.db", "sqlite path")
	out := fs.String("out", "/app/output/berth-report.json", "output path")
	if err := fs.Parse(args); err != nil {
		return err
	}

	store, err := db.Open(*dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	assignments, err := store.AllAssignments()
	if err != nil {
		return err
	}
	accepted, dup, err := store.ReplayStats()
	if err != nil {
		return err
	}

	overlaps := overlap.ConcurrentOverlapMinutes(assignments)
	dwell := overlap.TotalDwellMinutes(assignments)

	byBerth := map[string][]db.Assignment{}
	for _, a := range assignments {
		byBerth[a.BerthID] = append(byBerth[a.BerthID], a)
	}
	var berths []berthReport
	for berth, list := range byBerth {
		sort.Slice(list, func(i, j int) bool {
			if list[i].ArrivalUTC != list[j].ArrivalUTC {
				return list[i].ArrivalUTC < list[j].ArrivalUTC
			}
			return list[i].VoyageID < list[j].VoyageID
		})
		var views []assignmentView
		for _, a := range list {
			views = append(views, assignmentView{
				VoyageID:     a.VoyageID,
				MMSI:         a.MMSI,
				ArrivalUTC:   a.ArrivalUTC,
				DepartureUTC: a.DepartureUTC,
			})
		}
		berths = append(berths, berthReport{
			BerthID:                  berth,
			ConcurrentOverlapMinutes: overlaps[berth],
			TotalDwellMinutes:        dwell[berth],
			Assignments:              views,
		})
	}
	sort.Slice(berths, func(i, j int) bool { return berths[i].BerthID < berths[j].BerthID })

	digest, err := util.FileSHA256(staging.SnapshotPath)
	if err != nil {
		return fmt.Errorf("staging digest: %w", err)
	}

	rep := report{
		Berths: berths,
		ReplayStats: replayView{
			Accepted:          accepted,
			DuplicateRejected: dup,
		},
		StagingDigest: digest,
	}
	if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(*out, b, 0o644)
}
