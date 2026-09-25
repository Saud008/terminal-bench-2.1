package eval

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/terminus/bundlectl/internal/seed"
)

type EvalResult struct {
	Allow bool        `json:"allow"`
	Trace Trace       `json:"trace"`
}

type Trace struct {
	Bindings []Binding `json:"bindings"`
	Steps    []string  `json:"steps"`
}

type Binding struct {
	Ref   string          `json:"ref"`
	Value json.RawMessage `json:"value"`
}

func Run(bundleDir, seedStr, inputPath string) (*EvalResult, error) {
	policyPath := filepath.Join(bundleDir, "policies/allow.rego")
	raw, err := os.ReadFile(policyPath)
	if err != nil {
		return nil, err
	}
	expr, err := ParsePolicy(string(raw))
	if err != nil {
		return nil, err
	}
	dataBytes, err := os.ReadFile(filepath.Join(bundleDir, "data/data.json"))
	if err != nil {
		return nil, err
	}
	var data map[string]any
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		return nil, err
	}
	inRaw, err := os.ReadFile(inputPath)
	if err != nil {
		return nil, err
	}
	inRaw = seed.Apply(inRaw, seedStr)
	var input map[string]any
	if err := json.Unmarshal(inRaw, &input); err != nil {
		return nil, err
	}
	allow, err := evalExpr(expr, data, input)
	if err != nil {
		return nil, err
	}
	trace := BuildTrace(expr, data, input)
	result := &EvalResult{Allow: allow, Trace: trace}
	_ = WriteEvalAudit(bundleDir, seedStr, result)
	return result, nil
}

func evalExpr(expr Expr, data, input map[string]any) (bool, error) {
	lv, err := resolve(expr.Left, data, input)
	if err != nil {
		return false, err
	}
	rv, err := resolve(expr.Right, data, input)
	if err != nil {
		return false, err
	}
	return compare(lv, rv, expr.Op)
}

func resolve(ref string, data, input map[string]any) (float64, error) {
	if strings.HasPrefix(ref, "data.") {
		v, ok := data[strings.TrimPrefix(ref, "data.")]
		if !ok {
			return 0, fmt.Errorf("missing %s", ref)
		}
		return toFloat(v)
	}
	if strings.HasPrefix(ref, "input.") {
		v, ok := input[strings.TrimPrefix(ref, "input.")]
		if !ok {
			return 0, fmt.Errorf("missing %s", ref)
		}
		return toFloat(v)
	}
	return strconv.ParseFloat(ref, 64)
}

func toFloat(v any) (float64, error) {
	switch t := v.(type) {
	case float64:
		return t, nil
	case int:
		return float64(t), nil
	case int64:
		return float64(t), nil
	case json.Number:
		return t.Float64()
	case string:
		return strconv.ParseFloat(t, 64)
	default:
		return 0, fmt.Errorf("not numeric")
	}
}

func compare(l, r float64, op string) (bool, error) {
	switch op {
	case ">=":
		return l >= r, nil
	case ">":
		return l > r, nil
	case "<=":
		return l <= r, nil
	case "<":
		return l < r, nil
	case "==":
		return l == r, nil
	case "!=":
		return l != r, nil
	default:
		return false, fmt.Errorf("op %s", op)
	}
}
