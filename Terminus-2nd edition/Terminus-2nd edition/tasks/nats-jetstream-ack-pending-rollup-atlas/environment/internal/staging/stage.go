package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/natsjetstream/internal/types"
)

const DefaultStagePath = "/app/state/nats-jetstream-stage.json"

// NewEmpty returns an empty stage snapshot.
func NewEmpty() *types.StageFile {
	return &types.StageFile{
		Streams: map[string]*types.StreamState{},
	}
}

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

// Save writes stage state with stable formatting for tests.
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

// EnsureStream returns stream state, creating if needed.
func EnsureStream(st *types.StageFile, name string) *types.StreamState {
	if st.Streams[name] == nil {
		st.Streams[name] = &types.StreamState{
			Name:      name,
			Messages:  []types.StreamMessage{},
			Consumers: map[string]*types.ConsumerState{},
		}
	}
	return st.Streams[name]
}

// EnsureConsumer returns consumer state on a stream.
func EnsureConsumer(stream *types.StreamState, name string) *types.ConsumerState {
	if stream.Consumers[name] == nil {
		stream.Consumers[name] = &types.ConsumerState{
			Name:    name,
			Pending: map[uint64]types.PendingEntry{},
		}
	}
	return stream.Consumers[name]
}
