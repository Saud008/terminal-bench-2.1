package chronoclose

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/airclos/internal/amendlemma"
	"github.com/terminus/airclos/internal/bindvault"
	"github.com/terminus/airclos/internal/chronolemma"
	"github.com/terminus/airclos/internal/labtypes"
)

const chronoClosurePath = "/app/state/chronology-closure.json"

func Run(scenario string) error {
	binding, err := bindvault.ReadBinding("")
	if err != nil {
		return err
	}
	closed := amendlemma.CloseSeries(binding.Notams)
	var active []labtypes.NotamRecord
	for _, n := range closed {
		if chronolemma.ActiveAt(n.StartMin, n.EndMin, binding.Policy.EvalMinute) {
			active = append(active, n)
		}
	}
	out := labtypes.ChronologyClosure{
		Scenario:     scenario,
		ActiveNotams: active,
		EvalMinute:   binding.Policy.EvalMinute,
	}
	return writeClosure(chronoClosurePath, out)
}

func writeClosure(path string, out labtypes.ChronologyClosure) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadClosure(path string) (labtypes.ChronologyClosure, error) {
	if path == "" {
		path = chronoClosurePath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return labtypes.ChronologyClosure{}, err
	}
	var out labtypes.ChronologyClosure
	if err := json.Unmarshal(raw, &out); err != nil {
		return labtypes.ChronologyClosure{}, err
	}
	return out, nil
}
