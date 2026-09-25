package batchclosure

import (
	"github.com/terminus/termsetctl/internal/cutoff"
	"github.com/terminus/termsetctl/internal/fixturepack"
	"github.com/terminus/termsetctl/internal/journal"
	"github.com/terminus/termsetctl/internal/reversal"
	"github.com/terminus/termsetctl/internal/seal"
	"github.com/terminus/termsetctl/internal/seqguard"
	"github.com/terminus/termsetctl/internal/settlepromote"
	"github.com/terminus/termsetctl/internal/txnstate"
)

func CompileJournal(scenario, fixtureRoot string) error {
	batch, err := fixturepack.LoadScenario(scenario, fixtureRoot)
	if err != nil {
		return err
	}
	normalized := txnstate.NormalizeAll(batch.Transcripts)
	paired := reversal.PairReversals(normalized)
	finalized := settlepromote.FinalizeCapturedSales(paired)
	filtered := cutoff.FilterBatch(finalized, batch.CutoffEventMS)
	sorted := journal.SortRows(filtered)
	lines := seqguard.AssignSequences(sorted)
	auth := map[string]string{}
	for _, row := range sorted {
		auth[row.TxnID] = row.AuthCodeNorm
	}
	lines = journal.AttachDigests(batch.BatchID, lines, auth)
	return journal.WriteJournal(scenario, batch.BatchID, lines)
}

func SealSettlement(scenario, fixtureRoot string) error {
	batch, err := fixturepack.LoadScenario(scenario, fixtureRoot)
	if err != nil {
		return err
	}
	return seal.PublishFromMeta(batch)
}
