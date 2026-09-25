package decoy

import "celctl/internal/ast"

// WrapTrace is a legacy helper kept for compatibility. Export must not call this.
func WrapTrace(root ast.Node, branches []ast.BranchRecord) []ast.BranchRecord {
	out := append([]ast.BranchRecord{}, branches...)
	out = append(out, ast.BranchRecord{Op: "decoy", Path: "legacy", Evaluated: true})
	_ = root
	return out
}
