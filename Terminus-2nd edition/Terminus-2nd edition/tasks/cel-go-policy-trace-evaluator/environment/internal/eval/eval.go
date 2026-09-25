package eval

import (
	"encoding/json"
	"fmt"

	"celctl/internal/ast"
)

type Frame struct {
	Vars map[string]any
}

type Runtime struct {
	Env          map[string]any
	Frames       []Frame
	HasCallCount int
	Branches     []ast.BranchRecord
}

func NewRuntime(env map[string]any) *Runtime {
	cp := make(map[string]any, len(env))
	for k, v := range env {
		cp[k] = v
	}
	return &Runtime{Env: cp, Frames: []Frame{{Vars: map[string]any{}}}, Branches: []ast.BranchRecord{}}
}

func (r *Runtime) lookup(name string) (any, bool) {
	for i := len(r.Frames) - 1; i >= 0; i-- {
		if v, ok := r.Frames[i].Vars[name]; ok {
			return v, true
		}
	}
	v, ok := r.Env[name]
	return v, ok
}

func (r *Runtime) pushFrame() {
	r.Frames = append(r.Frames, Frame{Vars: map[string]any{}})
}

func (r *Runtime) popFrame() {
	if len(r.Frames) > 1 {
		r.Frames = r.Frames[:len(r.Frames)-1]
	}
}

func EvalNode(r *Runtime, node ast.Node, path string) (any, error) {
	switch node.Type {
	case "literal":
		return decodeLiteral(node)
	case "ident":
		v, ok := r.lookup(node.Name)
		if !ok {
			return false, nil
		}
		return v, nil
	case "binary":
		return evalBinary(r, node, path)
	case "call":
		return evalCall(r, node, path)
	case "map_comp":
		return evalMapComp(r, node, path)
	default:
		return nil, fmt.Errorf("unknown node type %q at %s", node.Type, path)
	}
}

func decodeLiteral(n ast.Node) (any, error) {
	switch n.Kind {
	case "bool":
		var b bool
		if err := json.Unmarshal(n.Value, &b); err != nil {
			return nil, err
		}
		return b, nil
	case "int":
		var i int64
		if err := json.Unmarshal(n.Value, &i); err != nil {
			return nil, err
		}
		return i, nil
	case "string", "duration":
		var s string
		if err := json.Unmarshal(n.Value, &s); err != nil {
			return nil, err
		}
		return s, nil
	default:
		return nil, fmt.Errorf("unknown literal kind %q", n.Kind)
	}
}

func evalBinary(r *Runtime, node ast.Node, path string) (any, error) {
	r.Branches = append(r.Branches, ast.BranchRecord{Op: node.Op, Path: path, Evaluated: true})
	if node.Left == nil || node.Right == nil {
		return nil, fmt.Errorf("binary missing operands at %s", path)
	}
	lv, err := EvalNode(r, *node.Left, path+".left")
	if err != nil {
		return nil, err
	}
	rv, err := EvalNode(r, *node.Right, path+".right")
	if err != nil {
		return nil, err
	}
	switch node.Op {
	case "and":
		return toBool(lv) && toBool(rv), nil
	case "or":
		return toBool(lv) || toBool(rv), nil
	case "eq":
		return lv == rv, nil
	case "lt", "gt":
		cmp, err := CompareDurationValues(lv, rv)
		if err != nil {
			return nil, err
		}
		if node.Op == "lt" {
			return cmp < 0, nil
		}
		return cmp > 0, nil
	default:
		return nil, fmt.Errorf("unknown op %q", node.Op)
	}
}

func evalCall(r *Runtime, node ast.Node, path string) (any, error) {
	r.Branches = append(r.Branches, ast.BranchRecord{Op: "call", Path: path, Evaluated: true})
	switch node.Fn {
	case "has":
		if len(node.Args) != 1 || node.Args[0].Type != "ident" {
			return nil, fmt.Errorf("has() expects ident arg")
		}
		r.HasCallCount++
		_, ok := r.lookup(node.Args[0].Name)
		return ok, nil
	case "cel.bind":
		if len(node.Args) != 3 {
			return nil, fmt.Errorf("cel.bind expects 3 args")
		}
		val, err := EvalNode(r, node.Args[0], path+".bind.val")
		if err != nil {
			return nil, err
		}
		if node.Args[1].Type != "ident" {
			return nil, fmt.Errorf("cel.bind var must be ident")
		}
		name := node.Args[1].Name
		r.pushFrame()
		r.Frames[len(r.Frames)-1].Vars[name] = val
		out, err := EvalNode(r, node.Args[2], path+".bind.body")
		r.popFrame()
		if len(r.Frames) > 1 {
			r.popFrame()
		}
		return out, err
	default:
		return nil, fmt.Errorf("unknown fn %q", node.Fn)
	}
}

func evalMapComp(r *Runtime, node ast.Node, path string) (any, error) {
	items, ok := r.lookup(node.Items)
	if !ok {
		return map[string]any{}, nil
	}
	list, ok := items.([]any)
	if !ok {
		return nil, fmt.Errorf("map_comp items must be list")
	}
	out := map[string]any{}
	for i, item := range list {
		r.pushFrame()
		r.Frames[len(r.Frames)-1].Vars["item"] = item
		key, err := EvalNode(r, *node.KeyExpr, fmt.Sprintf("%s.key.%d", path, i))
		r.popFrame()
		if err != nil {
			return nil, err
		}
		val, err := EvalNode(r, *node.ValueExpr, fmt.Sprintf("%s.val.%d", path, i))
		if err != nil {
			return nil, err
		}
		ks := fmt.Sprintf("%v", key)
		if _, exists := out[ks]; !exists {
			out[ks] = val
		}
	}
	return out, nil
}

func toBool(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case int:
		return t != 0
	case int64:
		return t != 0
	case float64:
		return t != 0
	default:
		return false
	}
}
