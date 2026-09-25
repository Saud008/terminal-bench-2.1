package shipment

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/originctl/internal/codify"
	"github.com/terminus/originctl/internal/ledger"
	"github.com/terminus/originctl/internal/model"
)

type Manifest struct {
	ScenarioID     string               `json:"scenario_id"`
	ShipmentDate   string               `json:"shipment_date"`
	ImporterID     string               `json:"importer_id"`
	Lines          []model.ShipmentLine `json:"lines"`
	Certificates   []model.Certificate  `json:"certificates"`
	AgreementRules []model.AgreementRule `json:"agreement_rules"`
}

func LoadManifest(name, fixtureDir string) (*Manifest, error) {
	path := filepath.Join(fixtureDir, "manifests", name+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var mf Manifest
	if err := json.Unmarshal(raw, &mf); err != nil {
		return nil, err
	}
	if mf.ScenarioID == "" {
		return nil, fmt.Errorf("scenario_id missing")
	}
	return &mf, nil
}

func ParseShipment(manifest, fixtureDir string) error {
	mf, err := LoadManifest(manifest, fixtureDir)
	if err != nil {
		return err
	}
	if err := persistManifest(mf); err != nil {
		return err
	}
	return writeNormalizedSnapshot(mf)
}

func persistManifest(mf *Manifest) error {
	db, err := ledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM lines`); err != nil {
		return err
	}
	if _, err := db.Exec(`DELETE FROM certificates`); err != nil {
		return err
	}
	if _, err := db.Exec(`DELETE FROM agreement_rules`); err != nil {
		return err
	}
	if err := ledger.SetMeta(db, "scenario_id", mf.ScenarioID); err != nil {
		return err
	}
	if err := ledger.SetMeta(db, "shipment_date", mf.ShipmentDate); err != nil {
		return err
	}
	if err := ledger.SetMeta(db, "importer_id", mf.ImporterID); err != nil {
		return err
	}
	for _, ln := range mf.Lines {
		bom, _ := json.Marshal(ln.BOMShares)
		_, err := db.Exec(`INSERT INTO lines(line_id,hs_norm,declared_origin,value_cents,bom_json) VALUES(?,?,?,?,?)`,
			ln.LineID, ln.HSRaw, ln.DeclaredOrigin, ln.ValueCents, string(bom))
		if err != nil {
			return err
		}
	}
	for _, cert := range mf.Certificates {
		_, err := db.Exec(`INSERT INTO certificates(cert_id,line_id,agreement_code,issued_on,expires_on,origin_country) VALUES(?,?,?,?,?,?)`,
			cert.CertID, cert.LineID, cert.AgreementCode, cert.IssuedOn, cert.ExpiresOn, cert.OriginCountry)
		if err != nil {
			return err
		}
	}
	for _, rule := range mf.AgreementRules {
		_, err := db.Exec(`INSERT INTO agreement_rules(agreement_code,hs_prefix,rvc_min_bps,duty_rate_bps,priority) VALUES(?,?,?,?,?)`,
			rule.AgreementCode, rule.HSPrefix, rule.RVCMinBPS, rule.DutyRateBPS, rule.Priority)
		if err != nil {
			return err
		}
	}
	return nil
}

func ManifestLoaded(manifest string) error {
	db, err := ledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	sid, err := ledger.GetMeta(db, "scenario_id")
	if err != nil {
		return err
	}
	if sid != manifest {
		return fmt.Errorf("manifest mismatch: loaded %s want %s", sid, manifest)
	}
	return nil
}

func writeNormalizedSnapshot(mf *Manifest) error {
	type snapLine struct {
		LineID       string `json:"line_id"`
		HSNormalized string `json:"hs_normalized"`
	}
	lines := make([]snapLine, 0, len(mf.Lines))
	for _, ln := range mf.Lines {
		lines = append(lines, snapLine{LineID: ln.LineID, HSNormalized: codify.NormalizeHS(ln.HSRaw)})
	}
	body := map[string]any{
		"scenario_id": mf.ScenarioID,
		"lines":       lines,
	}
	raw, err := json.MarshalIndent(body, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll("/app/var/workbench", 0o755); err != nil {
		return err
	}
	if err := os.WriteFile("/app/var/workbench/normalized-lines.json", raw, 0o644); err != nil {
		return err
	}
	return bumpParsePass()
}

func bumpParsePass() error {
	path := "/app/var/run/origin-pass.json"
	if err := os.MkdirAll("/app/var/run", 0o755); err != nil {
		return err
	}
	var body struct {
		ParsePass int `json:"parse_pass"`
		AtlasPass int `json:"atlas_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.ParsePass = body.ParsePass + 1
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}
