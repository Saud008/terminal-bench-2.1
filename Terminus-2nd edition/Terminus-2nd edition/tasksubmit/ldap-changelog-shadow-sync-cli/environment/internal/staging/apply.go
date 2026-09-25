package staging

import (
	"sort"

	"github.com/harbor/ldap-shadow-sync/internal/ldif"
	"github.com/harbor/ldap-shadow-sync/internal/model"
)

// ApplyRecord updates shadow state from one changelog record.
func ApplyRecord(shadow map[string]model.Entry, rec ldif.Record, normDN string) model.StagedChange {
	ch := model.StagedChange{
		NormalizedDN: normDN,
		ChangeNumber: rec.ChangeNumber,
		USNChanged:   rec.USNChanged,
		ChangeType:   rec.ChangeType,
		ModifyOps:    rec.ModifyOps,
	}
	switch rec.ChangeType {
	case "add":
		entry := model.Entry{
			NormalizedDN: normDN,
			Attrs:        copyAttrs(rec.Attrs),
			USNChanged:   rec.USNChanged,
		}
		shadow[normDN] = entry
		ch.Attrs = copyAttrs(entry.Attrs)
	case "delete":
		delete(shadow, normDN)
	case "modify":
		entry, ok := shadow[normDN]
		if !ok {
			entry = model.Entry{NormalizedDN: normDN, Attrs: map[string]string{}}
		}
		for _, op := range orderModifyOps(rec.ModifyOps) {
			applyModifyOp(&entry, op)
		}
		entry.USNChanged = rec.USNChanged
		shadow[normDN] = entry
		ch.Attrs = copyAttrs(entry.Attrs)
	}
	return ch
}

func applyModifyOp(entry *model.Entry, op model.ModifyOp) {
	if entry.Attrs == nil {
		entry.Attrs = map[string]string{}
	}
	switch op.Op {
	case "add":
		if len(op.Values) > 0 {
			entry.Attrs[op.Attr] = op.Values[0]
		}
	case "delete":
		delete(entry.Attrs, op.Attr)
	case "replace":
		delete(entry.Attrs, op.Attr)
		if len(op.Values) > 0 {
			entry.Attrs[op.Attr] = op.Values[0]
		}
	}
}

func copyAttrs(in map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range in {
		out[k] = v
	}
	return out
}

// orderModifyOps returns modify operations in application order.
func orderModifyOps(ops []model.ModifyOp) []model.ModifyOp {
	out := append([]model.ModifyOp{}, ops...)
	sort.SliceStable(out, func(i, j int) bool {
		return opRank(out[i].Op) < opRank(out[j].Op)
	})
	return out
}

func opRank(op string) int {
	if op == "delete" {
		return 0
	}
	return 1
}
