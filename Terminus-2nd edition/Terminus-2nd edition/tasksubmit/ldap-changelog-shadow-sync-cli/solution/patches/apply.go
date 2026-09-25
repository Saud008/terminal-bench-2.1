package staging

import (
	"strings"

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
	}
	switch rec.ChangeType {
	case "add":
		entry := model.Entry{
			NormalizedDN: normDN,
			Attrs:        canonAttrs(rec.Attrs),
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
		ops := canonModifyOps(rec.ModifyOps)
		ch.ModifyOps = ops
		for _, op := range ops {
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
	attr := strings.ToLower(op.Attr)
	switch op.Op {
	case "add":
		if len(op.Values) > 0 {
			entry.Attrs[attr] = op.Values[0]
		}
	case "delete":
		delete(entry.Attrs, attr)
	case "replace":
		delete(entry.Attrs, attr)
		if len(op.Values) > 0 {
			entry.Attrs[attr] = op.Values[0]
		}
	}
}

func canonAttrs(in map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range in {
		out[strings.ToLower(k)] = v
	}
	return out
}

func canonModifyOps(ops []model.ModifyOp) []model.ModifyOp {
	out := make([]model.ModifyOp, len(ops))
	for i, op := range ops {
		out[i] = model.ModifyOp{
			Op:     op.Op,
			Attr:   strings.ToLower(op.Attr),
			Values: append([]string{}, op.Values...),
		}
	}
	return out
}

func copyAttrs(in map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range in {
		out[k] = v
	}
	return out
}
