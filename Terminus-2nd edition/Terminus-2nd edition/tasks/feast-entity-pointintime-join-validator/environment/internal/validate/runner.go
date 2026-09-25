package validate

import (
	"os"
	"sort"
	"strconv"

	"github.com/terminus/feast-pit-join/internal/dedup"
	"github.com/terminus/feast-pit-join/internal/join"
	"github.com/terminus/feast-pit-join/internal/ledger"
	"github.com/terminus/feast-pit-join/internal/model"
	"github.com/terminus/feast-pit-join/internal/parity"
	"github.com/terminus/feast-pit-join/internal/partition"
	"github.com/terminus/feast-pit-join/internal/staging"
	"github.com/terminus/feast-pit-join/internal/ttl"
)

type Input struct {
	Seed, Scenario string
	StagingPath    string
	DBPath         string
}

func RunJoin(in Input) error {
	snap, err := staging.ReadSnapshot(in.StagingPath)
	if err != nil {
		return err
	}
	if err := staging.ValidateSeedScenario(snap, in.Seed, in.Scenario); err != nil {
		return err
	}
	store, err := ledger.Open(in.DBPath)
	if err != nil {
		return err
	}
	defer store.Close()
	if err := store.Reset(); err != nil {
		return err
	}

	ttlSec := snap.TTLSeconds
	if bias := os.Getenv("TB3_TTL_BIAS"); bias != "" {
		if b, err := strconv.ParseInt(bias, 10, 64); err == nil {
			ttlSec += b
		}
	}

	deduped, dupResolved := dedup.DeduplicateEvents(snap.Events)
	var ttlFiltered int
	var rows []model.ParityRow
	var asOfList []int64
	mismatch := 0

	for _, entry := range snap.AsOfEntries {
		asOfList = append(asOfList, entry.AsOfTS)
		filtered, tf := filterForAsOf(deduped, entry, ttlSec)
		ttlFiltered += tf
		targets := uniqueTargets(filtered)
		for _, t := range targets {
			off := join.SelectPIT(filtered, snap.EntityKeys, t.EntityID, t.DeviceID, t.SessionID, t.Feature, "offline", entry.AsOfTS)
			on := join.SelectPIT(filtered, snap.EntityKeys, t.EntityID, t.DeviceID, t.SessionID, t.Feature, "online", entry.AsOfTS)
			row := model.ParityRow{EntityID: t.EntityID, Feature: t.Feature, AsOfTS: entry.AsOfTS, MatchOK: true, Reason: "ok"}
			if off != nil {
				v := off.Value
				row.OfflineValue = &v
			}
			if on != nil {
				v := on.Value
				row.OnlineValue = &v
			}
			if row.OfflineValue == nil || row.OnlineValue == nil {
				row.MatchOK = false
				row.Reason = "missing_side"
				mismatch++
			} else if !parity.ValuesMatch(*row.OfflineValue, *row.OnlineValue) {
				row.MatchOK = false
				row.Reason = "value_mismatch"
				mismatch++
			}
			rows = append(rows, row)
		}
	}
	sort.Slice(asOfList, func(i, j int) bool { return asOfList[i] < asOfList[j] })
	parityOK := mismatch == 0
	runID, err := store.InsertRun(in.Seed, in.Scenario, snap.IngestSeq, parityOK)
	if err != nil {
		return err
	}
	for _, r := range rows {
		if err := store.InsertRow(runID, r); err != nil {
			return err
		}
	}
	sum := model.RunSummary{
		MismatchCount:       mismatch,
		TTLFilteredCount:    ttlFiltered,
		DuplicateTSResolved: dupResolved,
		AsOfTSList:          asOfList,
	}
	return store.InsertSummary(runID, sum)
}

type target struct {
	EntityID, DeviceID, SessionID, Feature string
}

func uniqueTargets(events []model.MaterializedEvent) []target {
	seen := map[string]target{}
	for _, ev := range events {
		k := ev.EntityID + "|" + ev.DeviceID + "|" + ev.SessionID + "|" + ev.Feature
		seen[k] = target{ev.EntityID, ev.DeviceID, ev.SessionID, ev.Feature}
	}
	out := make([]target, 0, len(seen))
	for _, v := range seen {
		out = append(out, v)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].EntityID != out[j].EntityID {
			return out[i].EntityID < out[j].EntityID
		}
		return out[i].Feature < out[j].Feature
	})
	return out
}

func filterForAsOf(events []model.MaterializedEvent, entry model.AsOfEntry, ttlSec int64) ([]model.MaterializedEvent, int) {
	out := make([]model.MaterializedEvent, 0, len(events))
	filtered := 0
	for _, ev := range events {
		if !ttl.WithinWindow(ev.EventTS, entry.AsOfTS, ttlSec) {
			filtered++
			continue
		}
		if !partition.Active(ev.Partition, entry.ActivePartition, nil) {
			continue
		}
		out = append(out, ev)
	}
	return out, filtered
}
