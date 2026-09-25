package replay

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/pulsar-dedup-replay/internal/broker"
	"github.com/terminus/pulsar-dedup-replay/internal/export"
	"github.com/terminus/pulsar-dedup-replay/internal/ingest"
	"github.com/terminus/pulsar-dedup-replay/internal/model"
	"github.com/terminus/pulsar-dedup-replay/internal/parse"
	"github.com/terminus/pulsar-dedup-replay/internal/sequence"
	"github.com/terminus/pulsar-dedup-replay/internal/staging"
)

type runtime struct {
	seenMsg map[string]map[string]struct{}
	seenSeq map[string]map[int64]struct{}
}

func newRuntime() *runtime {
	return &runtime{
		seenMsg: map[string]map[string]struct{}{},
		seenSeq: map[string]map[int64]struct{}{},
	}
}

func (rt *runtime) msgSeen(key, msgID string) bool {
	m, ok := rt.seenMsg[key]
	if !ok {
		return false
	}
	_, ok = m[msgID]
	return ok
}

func (rt *runtime) markMsg(key, msgID string) {
	if rt.seenMsg[key] == nil {
		rt.seenMsg[key] = map[string]struct{}{}
	}
	rt.seenMsg[key][msgID] = struct{}{}
}

func (rt *runtime) seqSeen(key string, seq int64) bool {
	m, ok := rt.seenSeq[key]
	if !ok {
		return false
	}
	_, ok = m[seq]
	return ok
}

func (rt *runtime) markSeq(key string, seq int64) {
	if rt.seenSeq[key] == nil {
		rt.seenSeq[key] = map[int64]struct{}{}
	}
	rt.seenSeq[key][seq] = struct{}{}
}

func initStream(snap *model.Snapshot, key string, epoch int) {
	if snap.Streams == nil {
		snap.Streams = map[string]model.StreamStats{}
	}
	if _, ok := snap.Streams[key]; !ok {
		snap.Streams[key] = model.StreamStats{Epoch: epoch}
	}
}

func ExportScenario(scenarioPath, outputPath string) error {
	sc, err := parse.LoadScenario(scenarioPath)
	if err != nil {
		return err
	}
	snap := model.Snapshot{
		Tenant:  sc.Tenant,
		Streams: map[string]model.StreamStats{},
	}
	rt := newRuntime()
	window := sc.DedupWindow

	for _, ev := range sc.Events {
		key := sequence.StreamKey(ev.Producer, ev.Topic)
		initStream(&snap, key, ev.Epoch)
		st := snap.Streams[key]

		if ev.Sequence < st.HighWater {
			if ingest.AllowSequenceReset(ev.Sequence, st.HighWater, ev.Epoch, st.Epoch) {
				st.Epoch = ev.Epoch
				st.HighWater = 0
				st.BrokerAckedMax = 0
				rt.seenMsg[key] = map[string]struct{}{}
				rt.seenSeq[key] = map[int64]struct{}{}
			} else {
				st.DedupMiss++
				snap.Streams[key] = st
				continue
			}
		}

		if rt.msgSeen(key, ev.MsgID) {
			NoteReplay(&st)
			snap.Streams[key] = st
			continue
		}

		if rt.seqSeen(key, ev.Sequence) {
			st.DedupMiss++
			snap.Streams[key] = st
			continue
		}

		if ev.Sequence < st.HighWater && !sequence.AcceptOutOfOrder(ev.Sequence, st.HighWater, window, rt.seenSeq[key]) {
			st.DedupMiss++
			snap.Streams[key] = st
			continue
		}

		if !ev.BrokerAck {
			st.DedupMiss++
			snap.Streams[key] = st
			continue
		}

		st.AcceptedCount++
		rt.markMsg(key, ev.MsgID)
		rt.markSeq(key, ev.Sequence)
		if ev.Sequence > st.HighWater {
			st.HighWater = ev.Sequence
		}
		if ev.Sequence > st.BrokerAckedMax {
			st.BrokerAckedMax = ev.Sequence
		}
		snap.Streams[key] = st
	}

	snap.StagingWritten = true
	snap.ExportBeforeAck = false
	acked := broker.MergeAck(snap.Streams)
	if err := broker.PersistAckedMax(acked); err != nil {
		return err
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return err
	}
	report, err := export.BuildReport(snap)
	if err != nil {
		return err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(outputPath, append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return nil
}

func ExportCLI(scenarioPath, outputPath string) int {
	if _, err := os.Stat(scenarioPath); err != nil {
		fmt.Fprintf(os.Stderr, "scenario not found: %s\n", scenarioPath)
		return 2
	}
	if err := ExportScenario(scenarioPath, outputPath); err != nil {
		fmt.Fprintf(os.Stderr, "export failed: %v\n", err)
		return 3
	}
	return 0
}
