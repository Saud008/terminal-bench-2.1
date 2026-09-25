package replay

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/fixdropcopy/internal/ledger"
	"github.com/terminus/fixdropcopy/internal/model"
	"github.com/terminus/fixdropcopy/internal/staging"
)

const generationPath = "/app/state/replay-generation.json"

type seqState struct {
	last int
}

func Run(scenarioID string) error {
	var snap model.StageSnapshot
	if err := staging.ReadStage(staging.DefaultStagePath, &snap); err != nil {
		return err
	}
	if snap.Scenario != scenarioID {
		return fmt.Errorf("staging scenario mismatch")
	}
	store, err := ledger.Open(ledger.DefaultDBPath)
	if err != nil {
		return err
	}
	defer store.Close()

	seq := map[string]seqState{}
	byFile := map[string][]model.StageEvent{}
	for _, ev := range snap.Events {
		byFile[ev.StreamFile] = append(byFile[ev.StreamFile], ev)
	}
	var files []string
	for f := range byFile {
		files = append(files, f)
	}
	sort.Strings(files)

	for _, file := range files {
		for _, ev := range byFile[file] {
			if ev.ResetSeq {
				seq[ev.Session] = seqState{last: 0}
				continue
			}
			st := seq[ev.Session]
			if ev.MsgSeq <= st.last {
				return fmt.Errorf("sequence regression session=%s seq=%d", ev.Session, ev.MsgSeq)
			}
			exists, err := store.HasExecID(ev.ClOrdID + ev.ExecID)
			if err != nil {
				return err
			}
			if exists {
				continue
			}
			row, err := buildRow(ev)
			if err != nil {
				return err
			}
			if err := store.InsertRow(row); err != nil {
				return err
			}
			if ev.ExecTransType == "1" && ev.OrigClOrdID != "" {
				_ = store.DeactivateByClOrdID(ev.OrigClOrdID)
			}
			if ev.ExecTransType == "2" && ev.OrigClOrdID != "" {
				_ = store.DeactivateByClOrdID(ev.OrigClOrdID)
				_ = store.DeactivateCancelsForOrig(ev.OrigClOrdID)
			}
			if ev.ExecType == "H" && ev.OrigClOrdID != "" {
				_ = store.DeactivateByClOrdID(ev.OrigClOrdID)
			}
			st.last = ev.MsgSeq
			seq[ev.Session] = st
		}
	}

	snap.ReplayGen++
	if err := staging.WriteStage(staging.DefaultStagePath, snap); err != nil {
		return err
	}
	gen := model.GenerationFile{ReplayGeneration: snap.ReplayGen}
	data, _ := json.MarshalIndent(gen, "", "  ")
	return os.WriteFile(generationPath, append(data, '\n'), 0o644)
}

func buildRow(ev model.StageEvent) (model.LedgerRow, error) {
	qty := ledger.SignedQty(ev.Side, ev.LastQty)
	if ev.ExecType == "H" {
		qty = int64(ev.LastQty)
	}
	return model.LedgerRow{
		ExecID:        ev.ExecID,
		Session:       ev.Session,
		ClOrdID:       ev.ClOrdID,
		OrigClOrdID:   ev.OrigClOrdID,
		ExecTransType: ev.ExecTransType,
		ExecType:      ev.ExecType,
		Symbol:        ev.Symbol,
		SignedQty:     qty,
		Active:        true,
		SendingTime:   ev.SendingTime,
		StreamFile:    ev.StreamFile,
	}, nil
}
