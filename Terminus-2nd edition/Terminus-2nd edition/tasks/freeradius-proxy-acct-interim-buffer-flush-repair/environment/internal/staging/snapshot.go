package staging

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/radiusproxy/internal/model"
)

const DefaultPath = "/app/state/acct-flush-snapshot.json"

func Write(path string, state *model.ProxyState, stats model.Stats) error {
	snap := Build(state, stats)
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

func Read(path string) (model.FlushSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.FlushSnapshot{}, err
	}
	var snap model.FlushSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.FlushSnapshot{}, err
	}
	return snap, nil
}

func Build(state *model.ProxyState, stats model.Stats) model.FlushSnapshot {
	sessions := exportSessions(state)
	queue := append([]model.FlushEntry(nil), state.FlushQueue...)
	if queue == nil {
		queue = []model.FlushEntry{}
	}
	sort.Slice(queue, func(i, j int) bool {
		if queue[i].SessionStartTS == queue[j].SessionStartTS {
			return queue[i].Seq < queue[j].Seq
		}
		return queue[i].SessionStartTS < queue[j].SessionStartTS
	})
	return model.FlushSnapshot{
		SnapshotVersion: 1,
		ProxyName:       state.ProxyName,
		HomeServer:      state.HomeServer,
		Sessions:        sessions,
		FlushQueue:      queue,
		Stats:           stats,
	}
}

func exportSessions(state *model.ProxyState) []model.SessionExport {
	keys := make([]model.SessionKey, 0, len(state.Sessions))
	for k := range state.Sessions {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		a, b := state.Sessions[keys[i]], state.Sessions[keys[j]]
		if a.SessionStartTS == b.SessionStartTS {
			if a.NASID == b.NASID {
				return a.AcctSessionID < b.AcctSessionID
			}
			return a.NASID < b.NASID
		}
		return a.SessionStartTS < b.SessionStartTS
	})
	out := make([]model.SessionExport, 0, len(keys))
	for _, k := range keys {
		s := state.Sessions[k]
		out = append(out, model.SessionExport{
			NASID:               s.NASID,
			AcctSessionID:       s.AcctSessionID,
			AcctUniqueSessionID: s.AcctUniqueSessionID,
			SessionStartTS:      s.SessionStartTS,
			InterimIntervalSec:  s.InterimIntervalSec,
			InputOctets:         s.InputOctets,
			OutputOctets:        s.OutputOctets,
			LastInterimTS:       s.LastInterimTS,
			Status:              s.Status,
		})
	}
	return out
}
