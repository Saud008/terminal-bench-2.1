package invoicepub

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/subledctl/internal/couponstack"
	"github.com/terminus/subledctl/internal/model"
	"github.com/terminus/subledctl/internal/store"
)

func PublishInvoices(scenario, outPath string) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	pass := readPass()
	_ = pass
	sid, err := store.GetMeta(db, "scenario_id")
	if err != nil {
		return err
	}
	cust, _ := store.GetMeta(db, "customer_id")
	segs, err := loadSegments(db)
	if err != nil {
		return err
	}
	coupons, _ := loadCoupons(db)
	lines := make([]model.InvoiceLine, 0)
	for _, s := range segs {
		overCents := int64(0)
		subtotal := s.BaseCents + overCents
		disc := couponstack.ApplyCoupons(subtotal, coupons)
		lines = append(lines, model.InvoiceLine{
			SegmentIndex:   s.SegmentIndex,
			LineKind:       "subscription",
			PlanID:         s.PlanID,
			BaseCents:      s.BaseCents,
			ProrationCents: 0,
			OverageCents:   overCents,
			CouponCents:    disc,
			TotalCents:     subtotal - disc,
		})
	}
	sort.Slice(lines, func(i, j int) bool {
		if lines[i].LineKind == lines[j].LineKind {
			return lines[i].SegmentIndex < lines[j].SegmentIndex
		}
		return lines[i].LineKind < lines[j].LineKind
	})
	digest := digestLines(lines)
	rep := model.InvoiceReport{
		ScenarioID:    sid,
		CustomerID:    cust,
		ReconcilePass: pass,
		InvoiceLines:  lines,
		LedgerDigest:  digest,
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if outPath == "" {
		outPath = "/app/output/subscription-invoices.json"
	}
	if err := os.WriteFile(outPath, raw, 0o644); err != nil {
		return err
	}
	jl, _ := json.Marshal(lines)
	return os.WriteFile("/app/output/entitlement-ledger.jsonl", append(jl, '\n'), 0o644)
}

type segRow struct {
	SegmentIndex int
	PlanID       string
	BaseCents    int64
}

func loadSegments(db *sql.DB) ([]segRow, error) {
	rs, err := db.Query(`SELECT segment_index,plan_id,base_cents FROM segments ORDER BY segment_index`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []segRow
	for rs.Next() {
		var s segRow
		if err := rs.Scan(&s.SegmentIndex, &s.PlanID, &s.BaseCents); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rs.Err()
}

func loadCoupons(db *sql.DB) ([]couponstack.Coupon, error) {
	rs, err := db.Query(`SELECT coupon_id,precedence,kind,value,stackable FROM coupons`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []couponstack.Coupon
	for rs.Next() {
		var c couponstack.Coupon
		var stack int
		if err := rs.Scan(&c.CouponID, &c.Precedence, &c.Kind, &c.Value, &stack); err != nil {
			return nil, err
		}
		c.Stackable = stack == 1
		out = append(out, c)
	}
	return out, rs.Err()
}

func readPass() int {
	raw, err := os.ReadFile("/app/state/reconcile-pass.json")
	if err != nil {
		return 0
	}
	var body struct {
		ReconcilePass int `json:"reconcile_pass"`
	}
	if json.Unmarshal(raw, &body) != nil {
		return 0
	}
	return body.ReconcilePass
}

func digestLines(lines []model.InvoiceLine) string {
	raw, _ := json.Marshal(lines)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}
