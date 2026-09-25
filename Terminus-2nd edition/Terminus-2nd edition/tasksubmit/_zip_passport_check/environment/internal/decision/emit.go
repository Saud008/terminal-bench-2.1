package decision

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/borderdocctl/internal/entrystamp"
	"github.com/terminus/borderdocctl/internal/model"
	"github.com/terminus/borderdocctl/internal/passport"
	"github.com/terminus/borderdocctl/internal/revoke"
	"github.com/terminus/borderdocctl/internal/rules"
	"github.com/terminus/borderdocctl/internal/store"
	"github.com/terminus/borderdocctl/internal/visa"
	"github.com/terminus/borderdocctl/internal/watchlist"
)

func EvaluateAll(scenario string) ([]model.DecisionRow, error) {
	db, err := store.Open()
	if err != nil {
		return nil, err
	}
	defer db.Close()

	ref, err := store.GetMeta(db, "reference_date")
	if err != nil {
		return nil, err
	}
	graceStr, _ := store.GetMeta(db, "grace_days")
	graceDays := 0
	fmt.Sscanf(graceStr, "%d", &graceDays)

	passports, err := loadPassports(db)
	if err != nil {
		return nil, err
	}
	visas, err := loadVisas(db)
	if err != nil {
		return nil, err
	}
	stamps, err := loadStamps(db)
	if err != nil {
		return nil, err
	}
	ruleRows, err := loadRules(db)
	if err != nil {
		return nil, err
	}
	holds, err := loadHolds(db)
	if err != nil {
		return nil, err
	}

	passByID := map[string]passportRow{}
	for _, p := range passports {
		passByID[p.DocID] = p
	}
	stampsByPass := map[string][]entrystamp.StampRow{}
	for _, st := range stamps {
		stampsByPass[st.PassportID] = append(stampsByPass[st.PassportID], entrystamp.StampRow{
			EntryDate: st.EntryDate,
			ExitDate:  st.ExitDate,
			PortCode:  st.PortCode,
		})
	}

	var out []model.DecisionRow
	for _, v := range visas {
		p, ok := passByID[v.PassportID]
		if !ok {
			continue
		}
		row := model.DecisionRow{
			HolderID:   p.HolderID,
			PassportID: p.DocID,
			VisaID:     v.DocID,
		}
		reasons := []string{}

		if !revoke.DocumentActive(v.Revoked, p.Revoked, true) {
			reasons = append(reasons, "document_revoked")
		}
		okPass, err := passport.PassportValidAt(ref, p.IssueDate, p.ExpiryDate)
		if err != nil {
			return nil, err
		}
		if !okPass {
			reasons = append(reasons, "passport_window")
		}
		okVisa, err := visa.VisaContainedInPassport(ref, v.ValidFrom, v.ValidTo, p.IssueDate, p.ExpiryDate)
		if err != nil {
			return nil, err
		}
		if !okVisa {
			reasons = append(reasons, "visa_overlap")
		}
		if watchlist.HasBlockingHold(p.HolderID, holds) {
			reasons = append(reasons, "watchlist_hold")
		}

		port := latestPort(stampsByPass[p.DocID])
		maxStay := rules.EffectiveMaxStay(port, ruleRows)
		cum, err := entrystamp.CumulativeStayDays(ref, stampsByPass[p.DocID], graceDays)
		if err != nil {
			return nil, err
		}
		row.CumulativeStayDays = cum
		row.MaxStayAllowed = maxStay
		remaining := maxStay - cum
		if remaining < 0 {
			remaining = 0
		}
		row.RemainingStayDays = remaining
		if maxStay > 0 && cum > maxStay+graceDays {
			reasons = append(reasons, "stay_exceeded")
		}

		row.DenyReasons = reasons
		row.AllowedEntry = len(reasons) == 0
		out = append(out, row)
	}

	sort.Slice(out, func(i, j int) bool {
		if out[i].HolderID == out[j].HolderID {
			return out[i].VisaID < out[j].VisaID
		}
		return out[i].HolderID < out[j].HolderID
	})
	return out, nil
}

func WriteDecisions(scenario string, rows []model.DecisionRow, outPath string) error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()

	sid, err := store.GetMeta(db, "scenario_id")
	if err != nil {
		return err
	}
	ref, err := store.GetMeta(db, "reference_date")
	if err != nil {
		return err
	}
	passNum := readEvalPass()

	if _, err := db.Exec(`DELETE FROM decisions`); err != nil {
		return err
	}
	for _, r := range rows {
		reasons, _ := json.Marshal(r.DenyReasons)
		allowed := 0
		if r.AllowedEntry {
			allowed = 1
		}
		_, err := db.Exec(`INSERT INTO decisions(holder_id,passport_id,visa_id,allowed_entry,deny_reasons,cumulative_stay_days,max_stay_allowed,remaining_stay_days) VALUES(?,?,?,?,?,?,?,?)`,
			r.HolderID, r.PassportID, r.VisaID, allowed, string(reasons), r.CumulativeStayDays, r.MaxStayAllowed, r.RemainingStayDays)
		if err != nil {
			return err
		}
	}

	digest := digestDecisions(rows)
	rep := model.DecisionReport{
		ScenarioID:    sid,
		EvalPass:      passNum,
		ReferenceDate: ref,
		Decisions:     rows,
		LedgerDigest:  digest,
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if outPath == "" {
		outPath = "/app/output/validity-decisions.json"
	}
	return os.WriteFile(outPath, raw, 0o644)
}

func digestDecisions(rows []model.DecisionRow) string {
	raw, _ := json.Marshal(rows)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func readEvalPass() int {
	raw, err := os.ReadFile("/app/state/eval-pass.json")
	if err != nil {
		return 0
	}
	var body struct {
		EvalPass int `json:"eval_pass"`
	}
	if json.Unmarshal(raw, &body) != nil {
		return 0
	}
	return body.EvalPass
}

func latestPort(stamps []entrystamp.StampRow) string {
	if len(stamps) == 0 {
		return ""
	}
	return stamps[len(stamps)-1].PortCode
}

type passportRow struct {
	DocID, HolderID, IssueDate, ExpiryDate string
	Revoked                                bool
}

type visaRow struct {
	DocID, PassportID, ValidFrom, ValidTo string
	Revoked                               bool
}

type stampRow struct {
	PassportID, EntryDate, ExitDate, PortCode string
}

func loadPassports(db *sql.DB) ([]passportRow, error) {
	rs, err := db.Query(`SELECT doc_id, holder_id, issue_date, expiry_date, revoked FROM passports ORDER BY doc_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []passportRow
	for rs.Next() {
		var p passportRow
		var rev int
		if err := rs.Scan(&p.DocID, &p.HolderID, &p.IssueDate, &p.ExpiryDate, &rev); err != nil {
			return nil, err
		}
		p.Revoked = rev == 1
		out = append(out, p)
	}
	return out, rs.Err()
}

func loadVisas(db *sql.DB) ([]visaRow, error) {
	rs, err := db.Query(`SELECT doc_id, passport_id, valid_from, valid_to, revoked FROM visas ORDER BY doc_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []visaRow
	for rs.Next() {
		var v visaRow
		var rev int
		if err := rs.Scan(&v.DocID, &v.PassportID, &v.ValidFrom, &v.ValidTo, &rev); err != nil {
			return nil, err
		}
		v.Revoked = rev == 1
		out = append(out, v)
	}
	return out, rs.Err()
}

func loadStamps(db *sql.DB) ([]stampRow, error) {
	rs, err := db.Query(`SELECT passport_id, entry_date, exit_date, port_code FROM stamps ORDER BY entry_date`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []stampRow
	for rs.Next() {
		var s stampRow
		if err := rs.Scan(&s.PassportID, &s.EntryDate, &s.ExitDate, &s.PortCode); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rs.Err()
}

func loadRules(db *sql.DB) ([]model.Rule, error) {
	rs, err := db.Query(`SELECT rule_id, scope, port_code, max_stay_days FROM rules ORDER BY rule_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []model.Rule
	for rs.Next() {
		var r model.Rule
		if err := rs.Scan(&r.RuleID, &r.Scope, &r.PortCode, &r.MaxStayDays); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rs.Err()
}

func loadHolds(db *sql.DB) ([]model.Hold, error) {
	rs, err := db.Query(`SELECT hold_id, holder_id, active, reason FROM holds ORDER BY hold_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []model.Hold
	for rs.Next() {
		var h model.Hold
		var active int
		if err := rs.Scan(&h.HoldID, &h.HolderID, &active, &h.Reason); err != nil {
			return nil, err
		}
		h.Active = active == 1
		out = append(out, h)
	}
	return out, rs.Err()
}
