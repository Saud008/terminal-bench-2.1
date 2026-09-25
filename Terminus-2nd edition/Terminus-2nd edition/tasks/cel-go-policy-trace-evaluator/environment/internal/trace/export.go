package trace

import (
	"encoding/json"
	"fmt"
	"os"

	"celctl/internal/ast"
	"celctl/internal/eval"
	"celctl/internal/staging"
)

func ExportEval(stagingPath string, env map[string]any, resultOut, traceOut string) error {
	snap, err := staging.LoadSnapshot(stagingPath)
	if err != nil {
		return err
	}
	rt := eval.NewRuntime(env)
	result, err := eval.EvalNode(rt, snap.Normalized, "root")
	if err != nil {
		return err
	}
	trace := ast.TraceFile{
		Result:       result,
		Branches:     rt.Branches,
		HasCallCount: rt.HasCallCount,
	}
	if traceOut != "" {
		if err := writeJSON(traceOut, trace); err != nil {
			return err
		}
	}
	if resultOut != "" {
		wrapper := map[string]any{"result": result}
		if err := writeJSON(resultOut, wrapper); err != nil {
			return err
		}
	}
	return nil
}

func writeJSON(path string, v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal %s: %w", path, err)
	}
	if err := os.MkdirAll(dirOf(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func dirOf(path string) string {
	for i := len(path) - 1; i >= 0; i-- {
		if path[i] == '/' {
			return path[:i]
		}
	}
	return "."
}
