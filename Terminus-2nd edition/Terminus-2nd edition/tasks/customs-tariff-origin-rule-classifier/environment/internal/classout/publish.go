package classout

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/originctl/internal/codify"
	"github.com/terminus/originctl/internal/ledger"
	"github.com/terminus/originctl/internal/model"
	"github.com/terminus/originctl/internal/concession"
	"github.com/terminus/originctl/internal/shipment"
)

func WriteAtlas(manifest, outPath string) error {
	if err := shipment.ManifestLoaded(manifest); err != nil {
		return err
	}
	db, err := ledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	pass := readParsePass()
	sid, err := ledger.GetMeta(db, "scenario_id")
	if err != nil {
		return err
	}
	shipDate, err := ledger.GetMeta(db, "shipment_date")
	if err != nil {
		return err
	}
	lines, err := loadLines(db)
	if err != nil {
		return err
	}
	certs, err := loadCerts(db)
	if err != nil {
		return err
	}
	rules, err := loadRules(db)
	if err != nil {
		return err
	}
	certByLine := map[string]certRow{}
	for _, c := range certs {
		certByLine[c.LineID] = c
	}
	var out []model.ClassificationLine
	for _, ln := range lines {
		hs := codify.NormalizeHS(ln.HSRaw)
		rvc := concession.RegionalValueBPS(ln.DeclaredOrigin, ln.BOMShares)
		rule := concession.PickAgreement(hs, rules)
		treatment := "mfn"
		agree := "MFN"
		duty := int64(500)
		certOK := false
		if rule != nil {
			agree = rule.AgreementCode
			duty = rule.DutyRateBPS
			if c, ok := certByLine[ln.LineID]; ok {
				certOK = concession.CertificateValid(shipDate, c.IssuedOn, c.ExpiresOn)
			}
			if certOK && concession.MeetsThreshold(rvc, rule.RVCMinBPS) {
				treatment = "preferential"
			}
		}
		out = append(out, model.ClassificationLine{
			LineID:          ln.LineID,
			HSNormalized:    hs,
			TariffTreatment: treatment,
			AgreementCode:   agree,
			RVCBPS:          rvc,
			CertValid:       certOK,
			DutyRateBPS:     duty,
		})
		_, _ = db.Exec(`INSERT INTO audit_rows(line_id,event_kind,detail,pass_num) VALUES(?,?,?,?)`,
			ln.LineID, treatment, agree, pass)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].LineID < out[j].LineID })
	digest := digestLines(out)
	rep := model.ClassificationReport{
		ScenarioID:      sid,
		ParsePass:       pass,
		Classifications: out,
		AuditDigest:     digest,
	}
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if outPath == "" {
		outPath = "/app/output/tariff-classifications.json"
	}
	if err := os.WriteFile(outPath, raw, 0o644); err != nil {
		return err
	}
	return writeAuditJSONL(out, pass)
}

type lineRow struct {
	LineID         string
	HSRaw          string
	DeclaredOrigin string
	BOMShares      []model.BOMShare
}

type certRow struct {
	LineID    string
	IssuedOn  string
	ExpiresOn string
}

func loadLines(db *sql.DB) ([]lineRow, error) {
	rs, err := db.Query(`SELECT line_id, hs_norm, declared_origin, bom_json FROM lines ORDER BY line_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []lineRow
	for rs.Next() {
		var lr lineRow
		var bomRaw string
		if err := rs.Scan(&lr.LineID, &lr.HSRaw, &lr.DeclaredOrigin, &bomRaw); err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(bomRaw), &lr.BOMShares)
		out = append(out, lr)
	}
	return out, rs.Err()
}

func loadCerts(db *sql.DB) ([]certRow, error) {
	rs, err := db.Query(`SELECT line_id, issued_on, expires_on FROM certificates`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []certRow
	for rs.Next() {
		var c certRow
		if err := rs.Scan(&c.LineID, &c.IssuedOn, &c.ExpiresOn); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rs.Err()
}

func loadRules(db *sql.DB) ([]concession.Rule, error) {
	rs, err := db.Query(`SELECT agreement_code, hs_prefix, rvc_min_bps, duty_rate_bps, priority FROM agreement_rules`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []concession.Rule
	for rs.Next() {
		var r concession.Rule
		if err := rs.Scan(&r.AgreementCode, &r.HSPrefix, &r.RVCMinBPS, &r.DutyRateBPS, &r.Priority); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rs.Err()
}

func readParsePass() int {
	raw, err := os.ReadFile("/app/var/run/origin-pass.json")
	if err != nil {
		return 0
	}
	var body struct {
		ParsePass int `json:"parse_pass"`
	}
	if json.Unmarshal(raw, &body) != nil {
		return 0
	}
	return body.ParsePass
}

func digestLines(lines []model.ClassificationLine) string {
	raw, _ := json.Marshal(lines)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func writeAuditJSONL(lines []model.ClassificationLine, pass int) error {
	path := "/app/output/origin-audit.jsonl"
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	for _, ln := range lines {
		row := map[string]any{
			"line_id":   ln.LineID,
			"treatment": ln.TariffTreatment,
			"pass_num":  pass,
		}
		raw, _ := json.Marshal(row)
		if _, err := fmt.Fprintf(f, "%s\n", raw); err != nil {
			return err
		}
	}
	return nil
}
