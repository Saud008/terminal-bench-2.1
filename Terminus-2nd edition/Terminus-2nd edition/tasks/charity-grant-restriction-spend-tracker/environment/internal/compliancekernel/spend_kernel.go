package compliancekernel

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/grantctl/internal/temporalceiling"
	"github.com/terminus/grantctl/internal/categoryguard"
	"github.com/terminus/grantctl/internal/codealias"
	"github.com/terminus/grantctl/internal/policyoverlap"
	"github.com/terminus/grantctl/internal/portfoliobundle"
	"github.com/terminus/grantctl/internal/atlaswriter"
	"github.com/terminus/grantctl/internal/store"
)

const passPath = "/app/state/amendment-pass.json"

type passState struct {
	AmendmentPass int `json:"amendment_pass"`
}

func LoadPortfolio(fixtureDir, scenario string) error {
	sc, err := portfoliobundle.ReadScenario(fixtureDir, scenario)
	if err != nil {
		return err
	}
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if err := store.ResetScenarioRows(db); err != nil {
		return err
	}
	if err := store.InsertScenario(db, sc); err != nil {
		return err
	}
	return writePass(passState{AmendmentPass: 0})
}

func ApplyAmendments() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()

	if _, err := db.Exec(`DELETE FROM staged_balances`); err != nil {
		return err
	}
	if _, err := db.Exec(`DELETE FROM staged_rejections`); err != nil {
		return err
	}

	grants, grantCategory, grantCeiling, err := readGrants(db)
	if err != nil {
		return err
	}
	aliases, err := readAliases(db)
	if err != nil {
		return err
	}
	expenses, err := readExpenses(db)
	if err != nil {
		return err
	}
	amendments, err := readAmendments(db)
	if err != nil {
		return err
	}
	spent := map[string]int64{}
	lastExpenseDate := map[string]string{}

	for _, e := range expenses {
		project := codealias.NormalizeProject(e.Project, aliases)
		cands := make([]policyoverlap.Candidate, 0, 4)
		for _, g := range grants {
			if g.Project != project {
				continue
			}
			if policyoverlap.RestrictionMatches(g.RestrictionPath, e.CategoryPath) {
				cands = append(cands, policyoverlap.Candidate{GrantID: g.GrantID, RestrictionPath: g.RestrictionPath})
			}
		}
		best, ok := policyoverlap.PickBest(cands)
		if !ok {
			if _, err := db.Exec(`INSERT INTO staged_rejections(expense_id, reason) VALUES(?, ?)`, e.ExpenseID, "no_restriction_match"); err != nil {
				return err
			}
			continue
		}
		if !categoryguard.AllowedCategory(e.Category, grantCategory[best.GrantID]) {
			if _, err := db.Exec(`INSERT INTO staged_rejections(expense_id, reason) VALUES(?, ?)`, e.ExpenseID, "category_rejected"); err != nil {
				return err
			}
			continue
		}
		spent[best.GrantID] += e.AmountCents
		lastExpenseDate[best.GrantID] = maxDate(lastExpenseDate[best.GrantID], e.ExpenseDate)
	}

	grantIDs := make([]string, 0, len(grantCeiling))
	for id := range grantCeiling {
		grantIDs = append(grantIDs, id)
	}
	sort.Strings(grantIDs)
	for _, grantID := range grantIDs {
		delta := temporalceiling.EligibleDelta(amendments, grantID, lastExpenseDate[grantID])
		remain := grantCeiling[grantID] + delta - spent[grantID]
		if _, err := db.Exec(
			`INSERT INTO staged_balances(grant_id, spent_cents, remaining_cents) VALUES(?, ?, ?)`,
			grantID, spent[grantID], remain,
		); err != nil {
			return err
		}
	}

	p := readPass()
	p.AmendmentPass++
	return writePass(p)
}

func PublishSpendAtlas() (atlaswriter.Atlas, error) {
	p := readPass()
	if p.AmendmentPass <= 0 {
		return atlaswriter.Atlas{}, errors.New("amendment_pass must be > 0 before publish")
	}
	db, err := store.Open()
	if err != nil {
		return atlaswriter.Atlas{}, err
	}
	defer db.Close()
	return atlaswriter.Publish(db, p.AmendmentPass)
}

type expenseRow struct {
	ExpenseID    string
	Project      string
	CategoryPath string
	Category     string
	ExpenseDate  string
	AmountCents  int64
}

type grantRow struct {
	GrantID         string
	Project         string
	RestrictionPath string
}

func readGrants(db *sql.DB) ([]grantRow, map[string][]string, map[string]int64, error) {
	rows, err := db.Query(`SELECT grant_id, project, restriction_path, allowed_categories_json, ceiling_cents FROM grants ORDER BY grant_id`)
	if err != nil {
		return nil, nil, nil, err
	}
	defer rows.Close()
	var out []grantRow
	category := map[string][]string{}
	ceiling := map[string]int64{}
	for rows.Next() {
		var g grantRow
		var catJSON string
		var ceilingCents int64
		if err := rows.Scan(&g.GrantID, &g.Project, &g.RestrictionPath, &catJSON, &ceilingCents); err != nil {
			return nil, nil, nil, err
		}
		var cats []string
		_ = json.Unmarshal([]byte(catJSON), &cats)
		out = append(out, g)
		category[g.GrantID] = cats
		ceiling[g.GrantID] = ceilingCents
	}
	return out, category, ceiling, nil
}

func readAliases(db *sql.DB) (map[string]string, error) {
	rows, err := db.Query(`SELECT alias, alias_of FROM project_aliases`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	m := map[string]string{}
	for rows.Next() {
		var a, c string
		if err := rows.Scan(&a, &c); err != nil {
			return nil, err
		}
		m[a] = c
	}
	return m, nil
}

func readExpenses(db *sql.DB) ([]expenseRow, error) {
	rows, err := db.Query(`SELECT expense_id, project, category_path, category, expense_date, amount_cents FROM expenses ORDER BY expense_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []expenseRow
	for rows.Next() {
		var e expenseRow
		if err := rows.Scan(&e.ExpenseID, &e.Project, &e.CategoryPath, &e.Category, &e.ExpenseDate, &e.AmountCents); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, nil
}

func readAmendments(db *sql.DB) ([]temporalceiling.Amendment, error) {
	rows, err := db.Query(`SELECT grant_id, effective_date, delta_cents FROM amendments ORDER BY amendment_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []temporalceiling.Amendment
	for rows.Next() {
		var a temporalceiling.Amendment
		if err := rows.Scan(&a.GrantID, &a.EffectiveDate, &a.DeltaCents); err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	return out, nil
}

func readPass() passState {
	body, err := os.ReadFile(passPath)
	if err != nil {
		return passState{AmendmentPass: 0}
	}
	var p passState
	if err := json.Unmarshal(body, &p); err != nil {
		return passState{AmendmentPass: 0}
	}
	return p
}

func writePass(p passState) error {
	body, _ := json.MarshalIndent(p, "", "  ")
	body = append(body, '\n')
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(passPath, body, 0o644)
}

func maxDate(a, b string) string {
	if a == "" {
		return b
	}
	if b > a {
		return b
	}
	return a
}

func ExplainError(err error) string {
	return fmt.Sprintf("grantctl pipeline error: %v", err)
}
