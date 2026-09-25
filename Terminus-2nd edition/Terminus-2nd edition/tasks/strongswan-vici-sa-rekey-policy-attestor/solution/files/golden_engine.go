package replay

import (
	"fmt"

	"github.com/terminus/vicireplay/internal/childsa"
	"github.com/terminus/vicireplay/internal/config"
	"github.com/terminus/vicireplay/internal/export"
	"github.com/terminus/vicireplay/internal/fsm"
	"github.com/terminus/vicireplay/internal/ikesa"
	"github.com/terminus/vicireplay/internal/ingest"
	"github.com/terminus/vicireplay/internal/model"
	"github.com/terminus/vicireplay/internal/sequence"
	"github.com/terminus/vicireplay/internal/staging"
)

type Result struct {
	Snapshot         model.RekeySnapshot
	RekeyRejectCount int
}

func Run(tr model.Trace) (Result, error) {
	tr = ingest.NormalizeTrace(tr)
	gate := fsm.NewRekeyGate()
	uids := ikesa.NewUIDMap()
	seq := sequence.NewTracker()
	children := map[int]model.ChildState{}
	var activeSpi uint64
	verdicts := []model.EventVerdict{}

	empty := model.RekeySnapshot{
		SnapshotVersion: 1,
		TableSuffix:     config.TableSuffix(),
		TraceID:         tr.TraceID,
		InitiatorOffset: config.InitiatorOffset(),
		Verdicts:        []model.EventVerdict{},
	}
	if err := staging.WriteEarlyManifest(empty); err != nil {
		return Result{}, err
	}

	for idx, ev := range tr.Events {
		rec := model.EventVerdict{
			EventIndex:   idx,
			LogSeq:       ev.LogSeq,
			OffsetMS:     ev.OffsetMS,
			EventType:    ev.Type,
			OrderOK:      true,
			SelectorsOK:  true,
			UidOK:        true,
			SeqMonotonic: true,
			Accepted:     true,
		}

		rec.SeqMonotonic = seq.Observe(ev.LogSeq, ev.Type == "child_rekey")
		if !rec.SeqMonotonic {
			rec.Accepted = false
			rec.RejectReason = "seq_not_monotonic"
		}

		switch ev.Type {
		case "ike_up":
			if !uids.Allocate(ev.IkeUniqueID) {
				rec.UidOK = false
				rec.Accepted = false
				rec.RejectReason = "uid_reused"
			}
		case "ike_down":
			uids.OnIkeDown(ev.IkeUniqueID)
		case "child_up":
			children[ev.ChildUniqueID] = model.ChildState{
				UniqueID: ev.ChildUniqueID,
				SpiIn:    ev.SpiIn,
				SpiOut:   ev.SpiOut,
				LocalTS:  append([]string(nil), ev.LocalTS...),
				RemoteTS: append([]string(nil), ev.RemoteTS...),
				Active:   true,
			}
			activeSpi = ev.SpiOut
		case "child_delete_request":
			gate.OnDeleteRequest(ev.ReqID)
		case "child_delete_response":
			gate.OnDeleteResponse(ev.ReqID)
			if c, ok := children[ev.ChildUniqueID]; ok {
				c.Deleted = true
				c.Active = false
				children[ev.ChildUniqueID] = c
			}
			activeSpi = export.PickActiveSpi(children)
		case "child_rekey":
			if !gate.OnRekeyInit() {
				rec.OrderOK = false
				rec.Accepted = false
				rec.RejectReason = "rekey_before_delete_ack"
			}
		case "child_rekey_done":
			old, ok := children[ev.ChildUniqueID]
			if ok {
				loc, rem := childsa.MergeSelectorsOnRekey(old.LocalTS, old.RemoteTS, ev.LocalTS, ev.RemoteTS)
				if !childsa.SupersetOK(old.LocalTS, loc) || !childsa.SupersetOK(old.RemoteTS, rem) {
					rec.SelectorsOK = false
					rec.Accepted = false
					rec.RejectReason = "selector_narrowed"
				}
				old.Deleted = true
				old.Active = false
				children[ev.ChildUniqueID] = old
			}
			newChild := model.ChildState{
				UniqueID: ev.ChildUniqueID,
				SpiIn:    ev.SpiIn,
				SpiOut:   ev.SpiOut,
				LocalTS:  append([]string(nil), ev.LocalTS...),
				RemoteTS: append([]string(nil), ev.RemoteTS...),
				Active:   true,
			}
			if ok {
				loc, rem := childsa.MergeSelectorsOnRekey(old.LocalTS, old.RemoteTS, ev.LocalTS, ev.RemoteTS)
				newChild.LocalTS = loc
				newChild.RemoteTS = rem
			}
			children[ev.ChildUniqueID] = newChild
			activeSpi = ev.SpiOut
		default:
			return Result{}, fmt.Errorf("unknown event type %q at index %d", ev.Type, idx)
		}

		if rec.Accepted && rec.RejectReason == "" {
			rec.ActiveSpiOut = activeSpi
		} else if len(verdicts) > 0 {
			rec.ActiveSpiOut = verdicts[len(verdicts)-1].ActiveSpiOut
		}
		verdicts = append(verdicts, rec)
	}

	activeSpi = export.PickActiveSpi(children)
	violations := export.BuildStats(verdicts)
	snap := model.RekeySnapshot{
		SnapshotVersion:     1,
		TableSuffix:         config.TableSuffix(),
		TraceID:             tr.TraceID,
		InitiatorOffset:     config.InitiatorOffset(),
		Verdicts:            verdicts,
		ActiveSpiOut:        activeSpi,
		RekeyViolationCount: violations,
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return Result{}, err
	}
	return Result{Snapshot: snap, RekeyRejectCount: violations}, nil
}
