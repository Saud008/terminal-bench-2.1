package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/harbor/fix-session-replay-ledger/internal/model"
)

const SnapshotPath = "/app/state/ingest-staging.json"

func WriteSnapshot(discoveryOrder []model.Execution, all []model.Execution) error {
	if err := os.MkdirAll(filepath.Dir(SnapshotPath), 0o755); err != nil {
		return err
	}
	frames := make([]model.StagingMessage, 0, len(discoveryOrder))
	for _, ex := range discoveryOrder {
		frames = append(frames, model.StagingMessage{
			SessionFile: ex.SessionFile,
			ClOrdID:     ex.ClOrdID,
			ExecID:      ex.ExecID,
			Symbol:      ex.Symbol,
			SendingTime: ex.SendingTime,
			MsgType:     ex.MsgType,
			ExecType:    ex.ExecType,
		})
	}
	snap := model.StagingSnapshot{
		MessageCount: len(all),
		Messages:     frames,
	}
	b, err := json.Marshal(snap)
	if err != nil {
		return err
	}
	return os.WriteFile(SnapshotPath, append(b, '\n'), 0o644)
}
