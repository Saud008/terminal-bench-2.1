package orchestrate

import (
	"github.com/terminus/coreidx/internal/crashfold"
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/symcatalog"
)

func stageOne(rec model.CrashRecord, cat *symcatalog.Index) (model.StagedCrash, error) {
	topPC := ""
	topModule := ""
	if len(rec.Threads) > 0 && len(rec.Threads[0].Frames) > 0 {
		topPC = rec.Threads[0].Frames[0].PC
		topModule = rec.Threads[0].Frames[0].Module
	}
	buildID := pcBuildID(topPC, rec.Mmap)
	entry, buildID := catalogEntryFor(buildID, topModule, rec.Mmap, cat)
	var resolved []model.ResolvedFrame
	for _, th := range rec.Threads {
		for _, fr := range th.Frames {
			sym := resolveFrame(fr, rec.Mmap, entry, cat)
			resolved = append(resolved, model.ResolvedFrame{
				PC: fr.PC, Module: fr.Module, Symbol: sym,
			})
		}
	}
	topSymbol := ""
	if len(resolved) > 0 {
		topSymbol = resolved[0].Symbol
	}
	gk := crashfold.GroupKey(rec, topPC, buildID, topSymbol)
	return model.StagedCrash{
		CrashID: rec.CrashID, Timestamp: rec.Timestamp, Signal: rec.Signal, PID: rec.PID,
		GroupKey: gk, BuildID: buildID, TopSymbol: topSymbol, Frames: resolved,
	}, nil
}
