package eval

import (
	"encoding/json"
	"os"
)

type EvalAudit struct {
	Bundle        string `json:"bundle"`
	Seed          string `json:"seed"`
	Allow         bool   `json:"allow"`
	BindingCount  int    `json:"binding_count"`
}

const evalAuditPath = "/app/state/eval-audit.json"

func WriteEvalAudit(bundleDir, seed string, res *EvalResult) error {
	audit := EvalAudit{
		Bundle:       bundleDir,
		Seed:         seed,
		Allow:        res.Allow,
		BindingCount: len(res.Trace.Bindings) - 1,
	}
	if audit.BindingCount < 0 {
		audit.BindingCount = 0
	}
	raw, err := json.MarshalIndent(audit, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(evalAuditPath, raw, 0o644)
}

func LoadEvalAudit() (*EvalAudit, error) {
	raw, err := os.ReadFile(evalAuditPath)
	if err != nil {
		return nil, err
	}
	var audit EvalAudit
	if err := json.Unmarshal(raw, &audit); err != nil {
		return nil, err
	}
	return &audit, nil
}
