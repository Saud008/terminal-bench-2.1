package proof

import (
	"strings"

	"nsecval/internal/model"
	"nsecval/internal/nsec3"
	"nsecval/internal/stub"
	"nsecval/internal/wire"
)

type Walker struct {
	Zone    string
	Records []model.Record
	Params  model.NSEC3Params
	Cache   *stub.Cache
}

func (w *Walker) ValidateQuery(q model.Query) (model.QueryResult, bool, error) {
	if hit, ok := w.Cache.Get(q.Qname); ok {
		return hit, true, nil
	}
	status, proofKind := w.walk(q)
	res := model.QueryResult{Qname: q.Qname, Qtype: q.Qtype, Status: status, Proof: proofKind}
	w.Cache.Put(q.Qname, res)
	return res, false, nil
}

func (w *Walker) walk(q model.Query) (string, string) {
	qname := wire.EnsureTrailingDot(q.Qname)
	if w.tryWildcard(qname, q.Qtype) {
		return matchStatus(q.Expect), "wildcard"
	}
	if w.coversNSEC(qname, q.Qtype) {
		return matchStatus(q.Expect), "nsec"
	}
	if w.coversNSEC3(qname) {
		return matchStatus(q.Expect), "nsec3"
	}
	if q.Expect == "invalid" {
		return "invalid", "none"
	}
	return "invalid", "none"
}

func matchStatus(expect string) string {
	if expect == "invalid" {
		return "invalid"
	}
	return "valid"
}

func (w *Walker) tryWildcard(qname, qtype string) bool {
	_ = qtype
	for _, r := range w.Records {
		if r.Rtype != "NSEC" {
			continue
		}
		owner := wire.Canonical(r.Owner)
		if strings.HasPrefix(owner, "*.") {
			suffix := strings.TrimPrefix(owner, "*.")
			if strings.HasSuffix(wire.Canonical(qname), suffix) {
				return true
			}
		}
	}
	return false
}

func (w *Walker) coversNSEC(qname, qtype string) bool {
	qc := wire.Canonical(qname)
	for _, r := range w.Records {
		if r.Rtype != "NSEC" {
			continue
		}
		owner := wire.Canonical(r.Owner)
		next := wire.Canonical(r.Next)
		if owner < qc && qc < next {
			for _, t := range r.TypeBitmap {
				if t == qtype {
					return false
				}
			}
			return true
		}
	}
	return false
}

func (w *Walker) coversNSEC3(qname string) bool {
	for _, r := range w.Records {
		if nsec3.CoversQname(r, qname, w.Params) {
			return true
		}
	}
	return false
}
