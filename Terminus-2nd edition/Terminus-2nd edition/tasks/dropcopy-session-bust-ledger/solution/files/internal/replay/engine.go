package replay

import (
	"database/sql"
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
	last       int
	allowReset bool
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
		if err := replayFile(store, seq, byFile[file]); err != nil {
			return err
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

func replayFile(store *ledger.Store, seq map[string]seqState, events []model.StageEvent) error {
	tx, err := store.BeginBatch()
	if err != nil {
		return err
	}
	localSeq := copySeq(seq)
	for _, ev := range events {
		if ev.ResetSeq {
			localSeq[ev.Session] = seqState{last: 0, allowReset: true}
			continue
		}
		st := localSeq[ev.Session]
		if ev.MsgSeq <= st.last && !st.allowReset {
			tx.Rollback()
			return fmt.Errorf("sequence regression session=%s seq=%d", ev.Session, ev.MsgSeq)
		}
		exists, err := ledger.HasExecIDTx(tx, ev.ExecID)
		if err != nil {
			tx.Rollback()
			return err
		}
		if exists {
			continue
		}
		row, err := buildRow(tx, ev)
		if err != nil {
			tx.Rollback()
			return err
		}
		if err := ledger.InsertRowTx(tx, row); err != nil {
			tx.Rollback()
			return err
		}
		if ev.ExecTransType == "2" && ev.OrigClOrdID != "" {
			if err := ledger.DeactivateCancelsForOrigTx(tx, ev.OrigClOrdID); err != nil {
				tx.Rollback()
				return err
			}
		}
		if ev.ExecTransType == "1" && ev.OrigClOrdID != "" {
			if err := ledger.DeactivateByClOrdIDTx(tx, ev.OrigClOrdID); err != nil {
				tx.Rollback()
				return err
			}
		}
		// Trade bust (150=H) keeps the original fill active and posts a reversing
		// signed qty so net position returns to zero without deactivating the fill.
		localSeq[ev.Session] = seqState{last: ev.MsgSeq, allowReset: false}
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	for k, v := range localSeq {
		seq[k] = v
	}
	return nil
}

func copySeq(in map[string]seqState) map[string]seqState {
	out := map[string]seqState{}
	for k, v := range in {
		out[k] = v
	}
	return out
}

func buildRow(tx *sql.Tx, ev model.StageEvent) (model.LedgerRow, error) {
	qty := ledger.SignedQty(ev.Side, ev.LastQty)
	if ev.ExecType == "H" {
		ref, err := ledger.LookupSignedQtyTx(tx, ev.OrigClOrdID)
		if err != nil {
			return model.LedgerRow{}, err
		}
		qty = -ref
	}
	if ev.ExecTransType == "2" {
		qty = ledger.SignedQty(ev.Side, ev.LastQty)
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
