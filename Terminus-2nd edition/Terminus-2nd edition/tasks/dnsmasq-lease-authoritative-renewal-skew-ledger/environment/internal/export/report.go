package export

import (
	"encoding/json"
	"os"
	"sort"

	"dnsmasqledger/internal/journal"
	"dnsmasqledger/internal/model"
)

const snapshotPath = "/app/state/lease-snapshot.json"

func WriteSnapshot(cat *model.Catalog) error {
	snap := model.Snapshot{
		NowSec:        cat.NowSec,
		ActiveCount:   len(cat.Leases),
		DNSForward:    copyMap(cat.DNSForward),
		CheckpointSeq: cat.Checkpoint,
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(snapshotPath, data, 0o644)
}

func BuildReport(cat *model.Catalog, applied int) model.LeaseReport {
	rows := make([]model.LeaseRow, 0, len(cat.Leases))
	for _, l := range cat.Leases {
		if !l.Authoritative {
			continue
		}
		rows = append(rows, model.LeaseRow{
			IdentityKey:   l.IdentityKey,
			MAC:           l.MAC,
			DUID:          l.DUID,
			IAID:          l.IAID,
			Hostname:      l.Hostname,
			IP:            l.IP,
			ExpiresSec:    l.ExpiresSec,
			Authoritative: l.Authoritative,
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].IdentityKey == rows[j].IdentityKey {
			return rows[i].Hostname < rows[j].Hostname
		}
		return rows[i].IdentityKey < rows[j].IdentityKey
	})
	return model.LeaseReport{
		LogPath:        cat.LogPath,
		NowSec:         cat.NowSec,
		ActiveLeases:   rows,
		DNSForward:     copyMap(cat.DNSForward),
		JournalTail:    journal.Tail(cat, 8),
		CheckpointSeq:  cat.Checkpoint,
		EventsApplied:  applied,
		TentativeCount: len(cat.Tentative),
	}
}

func WriteReport(path string, rep model.LeaseReport) error {
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func copyMap(in map[string]string) map[string]string {
	out := make(map[string]string, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}
