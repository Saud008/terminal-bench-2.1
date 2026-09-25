package ingest

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/harbor/tug-berth/internal/db"
	"github.com/harbor/tug-berth/internal/model"
	"github.com/harbor/tug-berth/internal/nmea"
	"github.com/harbor/tug-berth/internal/staging"
)

func Run(args []string) error {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	input := fs.String("input", "", "jsonl path")
	dbPath := fs.String("db", "/app/state/berth.db", "sqlite path")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *input == "" {
		return fmt.Errorf("--input required")
	}

	store, err := db.Open(*dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	f, err := os.Open(*input)
	if err != nil {
		return err
	}
	defer f.Close()

	var snap []model.SnapshotRow
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var row model.DispatchRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return err
		}
		if !nmea.ValidateChecksum(row.NmeaRaw) {
			return fmt.Errorf("invalid nmea checksum for voyage %s", row.VoyageID)
		}
		parsed, err := nmea.ParseMMSIFromVDM(row.NmeaRaw)
		if err != nil {
			return err
		}
		if parsed != row.MMSI {
			return fmt.Errorf("mmsi mismatch for voyage %s", row.VoyageID)
		}
		key := db.IdempotencyKey(row.VoyageID, row.BerthID, row.ArrivalUTC)
		a := db.Assignment{
			VoyageID:     row.VoyageID,
			MMSI:         row.MMSI,
			BerthID:      row.BerthID,
			ArrivalUTC:   row.ArrivalUTC,
			DepartureUTC: row.DepartureUTC,
		}
		ok, err := store.InsertAssignment(a, key)
		if err != nil {
			if strings.Contains(err.Error(), "UNIQUE") {
				_ = store.RecordDuplicate()
				continue
			}
			return err
		}
		if ok {
			snap = append(snap, model.SnapshotRow{
				VoyageID:     row.VoyageID,
				MMSI:         row.MMSI,
				BerthID:      row.BerthID,
				ArrivalUTC:   row.ArrivalUTC,
				DepartureUTC: row.DepartureUTC,
			})
		}
	}
	if err := sc.Err(); err != nil {
		return err
	}
	return staging.WriteSnapshot(snap)
}
