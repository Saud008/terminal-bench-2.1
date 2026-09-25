package witness

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strconv"

	"github.com/terminus/livattest-gate/internal/store"
)

const SnapshotPath = "/app/state/witness-snapshot.json"

type Snapshot struct {
	Version          int    `json:"version"`
	Token            string `json:"token"`
	SessionID        string `json:"session_id"`
	WitnessSeq       int    `json:"witness_seq"`
	WitnessHead      string `json:"witness_head"`
	BreachesOpened   int    `json:"breaches_opened"`
	BreachesClosed   int    `json:"breaches_closed"`
	MissingSpanTotal int    `json:"missing_span_total"`
	RepairEvents     int    `json:"repair_events"`
	ActiveBanSeals   int    `json:"active_ban_seals"`
	LastSeq          uint32 `json:"last_seq"`
	SkewRejections   int    `json:"skew_rejections,omitempty"`
	DupRejections    int    `json:"duplicate_rejections,omitempty"`
	TicketRejections int    `json:"ticket_rejections,omitempty"`
}

func WriteSnapshot(st *store.Store, token, sessionID string) error {
	return PersistSnapshot(st, token, sessionID)
}

func ReadSnapshot() (Snapshot, error) {
	data, err := os.ReadFile(SnapshotPath)
	if err != nil {
		return Snapshot{}, err
	}
	var snap Snapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return Snapshot{}, err
	}
	return snap, nil
}

func ComputeHead(prevHead, token, sessionID string, lastSeq uint32, witnessSeq int) string {
	msg := prevHead + ":" + token + ":" + sessionID + ":" + strconv.FormatUint(uint64(lastSeq), 10) + ":" + strconv.Itoa(witnessSeq)
	sum := sha256.Sum256([]byte(msg))
	return hex.EncodeToString(sum[:])
}

func writeSnapshotFile(snap Snapshot) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(SnapshotPath, append(raw, '\n'), 0o644)
}

func BuildSnapshot(st *store.Store, token, sessionID string) (Snapshot, error) {
	sess, err := st.GetSession(token, sessionID)
	if err != nil {
		return Snapshot{}, err
	}
	opened, closed, spanTotal, repairs, err := st.Counters(token, sessionID)
	if err != nil {
		return Snapshot{}, err
	}
	bans, err := st.CountActiveBans(token, sessionID)
	if err != nil {
		return Snapshot{}, err
	}
	prevHead := ""
	witnessSeq := 1
	if prev, err := ReadSnapshot(); err == nil && prev.Token == token && prev.SessionID == sessionID {
		prevHead = prev.WitnessHead
		witnessSeq = prev.WitnessSeq + 1
	}
	lastSeq := uint32(0)
	if sess.HasLastSeq {
		lastSeq = sess.LastSeq
	}
	head := ComputeHead(prevHead, token, sessionID, lastSeq, witnessSeq)
	return Snapshot{
		Version:          1,
		Token:            token,
		SessionID:        sessionID,
		WitnessSeq:       witnessSeq,
		WitnessHead:      head,
		BreachesOpened:   opened,
		BreachesClosed:   closed,
		MissingSpanTotal: spanTotal,
		RepairEvents:     repairs,
		ActiveBanSeals:   bans,
		LastSeq:          lastSeq,
		SkewRejections:   sess.SkewRejects,
		DupRejections:    sess.DupRejects,
		TicketRejections: sess.TicketRejects,
	}, nil
}

func PersistSnapshot(st *store.Store, token, sessionID string) error {
	snap, err := BuildSnapshot(st, token, sessionID)
	if err != nil {
		return err
	}
	if err := writeSnapshotFile(snap); err != nil {
		return fmt.Errorf("witness stage: %w", err)
	}
	return nil
}
