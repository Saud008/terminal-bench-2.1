package pipeline

import (
	"github.com/terminus/ppareconctl/internal/invoicepublish"
	"github.com/terminus/ppareconctl/internal/scenarioload"
	"github.com/terminus/ppareconctl/internal/settlementlines"
)

// MaterializeLines aligns intervals and persists settlement line rows to disk.
func MaterializeLines(scenario, fixtureRoot string) error {
	sc, err := scenarioload.LoadScenario(scenario, fixtureRoot)
	if err != nil {
		return err
	}
	lines, err := settlementlines.BuildLines(sc)
	if err != nil {
		return err
	}
	return settlementlines.Persist(scenario, sc, lines)
}

// RollupBillingInvoice rolls up persisted lines into invoice JSON.
func RollupBillingInvoice(scenario, fixtureRoot string) error {
	sc, err := scenarioload.LoadScenario(scenario, fixtureRoot)
	if err != nil {
		return err
	}
	return invoicepublish.Publish(scenario, sc)
}
