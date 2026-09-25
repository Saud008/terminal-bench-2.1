package proof

import "nsecval/internal/model"

// WrapDenial is a legacy helper kept for diagnostics; production validate uses Walker.
func WrapDenial(q model.Query, status, proofKind string) model.QueryResult {
	return model.QueryResult{
		Qname:  q.Qname,
		Qtype:  q.Qtype,
		Status: status,
		Proof:  proofKind,
	}
}
