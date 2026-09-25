package ast

import "encoding/json"

type Node struct {
	Type     string          `json:"type"`
	Kind     string          `json:"kind,omitempty"`
	Value    json.RawMessage `json:"value,omitempty"`
	Name     string          `json:"name,omitempty"`
	Fn       string          `json:"fn,omitempty"`
	Args     []Node          `json:"args,omitempty"`
	Op       string          `json:"op,omitempty"`
	Left     *Node           `json:"left,omitempty"`
	Right    *Node           `json:"right,omitempty"`
	KeyExpr  *Node           `json:"key_expr,omitempty"`
	ValueExpr *Node          `json:"value_expr,omitempty"`
	Items    string          `json:"items,omitempty"`
}

type InputFile struct {
	Root Node `json:"root"`
}

type StagingFile struct {
	Version    int    `json:"version"`
	Source     string `json:"source"`
	ASTHash    string `json:"ast_hash"`
	Normalized Node   `json:"normalized"`
}

type TraceFile struct {
	Result       any              `json:"result"`
	Branches     []BranchRecord   `json:"branches"`
	HasCallCount int              `json:"has_call_count"`
}

type BranchRecord struct {
	Op        string `json:"op"`
	Path      string `json:"path"`
	Evaluated bool   `json:"evaluated"`
}
