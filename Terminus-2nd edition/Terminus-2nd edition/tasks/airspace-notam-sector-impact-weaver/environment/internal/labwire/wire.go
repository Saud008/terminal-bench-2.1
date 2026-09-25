package labwire

import (
	"github.com/terminus/airclos/internal/atlasseal"
	"github.com/terminus/airclos/internal/bindvault"
	"github.com/terminus/airclos/internal/campaignio"
	"github.com/terminus/airclos/internal/chronoclose"
	"github.com/terminus/airclos/internal/labtypes"
	"github.com/terminus/airclos/internal/latticefold"
)

func BindCampaign(scenario, fixtureRoot string) (labtypes.CampaignBinding, error) {
	notams, sectors, flights, airways, fixes, policy, err := campaignio.LoadScenario(scenario, fixtureRoot)
	if err != nil {
		return labtypes.CampaignBinding{}, err
	}
	return labtypes.CampaignBinding{
		Engine:    "airclos",
		Scenario:  scenario,
		Notams:    notams,
		Sectors:   sectors,
		Flights:   flights,
		Airways:   airways,
		FixPoints: fixes,
		Policy:    policy,
	}, nil
}

func PersistBinding(binding labtypes.CampaignBinding) error {
	return bindvault.WriteBinding("", binding)
}

func RunCloseChronology(scenario string) error {
	return chronoclose.Run(scenario)
}

func RunFoldClosure(scenario string) error {
	return latticefold.Run(scenario)
}

func SealAtlas(scenario, outPath string) error {
	return atlasseal.Publish(scenario, outPath)
}
