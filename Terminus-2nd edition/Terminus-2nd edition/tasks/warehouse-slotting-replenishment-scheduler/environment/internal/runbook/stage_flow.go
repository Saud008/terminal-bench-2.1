package runbook

import (
	"github.com/terminus/whslot/internal/waveplanner"
	"github.com/terminus/whslot/internal/crewwindow"
	"github.com/terminus/whslot/internal/pickspeed"
	"github.com/terminus/whslot/internal/yardfeed"
)

func LatchYard(scenario, fixtureDir string) error {
	return yardfeed.LatchScenario(scenario, fixtureDir)
}

func RankVelocity() error { return pickspeed.Run() }

func PlanReplen() error { return waveplanner.Run() }

func BindShifts() error { return crewwindow.Run() }
