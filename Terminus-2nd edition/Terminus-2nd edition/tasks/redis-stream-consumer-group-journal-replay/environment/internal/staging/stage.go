package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/redisstream/internal/types"
)

const DefaultStagePath = "/app/state/redis-stream-stage.json"

// Load reads a stage file from disk.
func Load(path string) (*types.StageFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var st types.StageFile
	if err := json.Unmarshal(data, &st); err != nil {
		return nil, err
	}
	return &st, nil
}

// Save writes stage state with stable key ordering for tests.
func Save(path string, st *types.StageFile) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

// NewEmpty returns an empty stage snapshot.
func NewEmpty() *types.StageFile {
	return &types.StageFile{
		Streams:    map[string]*types.StreamState{},
		PendingLog: []types.PendingAdvance{},
	}
}

// EnsureStream returns stream state, creating if needed.
func EnsureStream(st *types.StageFile, name string) *types.StreamState {
	if st.Streams[name] == nil {
		st.Streams[name] = &types.StreamState{
			Name:   name,
			Groups: map[string]*types.ConsumerGroup{},
		}
	}
	return st.Streams[name]
}

// EnsureGroup returns group state on a stream.
func EnsureGroup(stream *types.StreamState, group string) *types.ConsumerGroup {
	if stream.Groups[group] == nil {
		stream.Groups[group] = &types.ConsumerGroup{
			Name:    group,
			LastID:  "0-0",
			Pending: map[string]types.PELMessage{},
		}
	}
	return stream.Groups[group]
}
