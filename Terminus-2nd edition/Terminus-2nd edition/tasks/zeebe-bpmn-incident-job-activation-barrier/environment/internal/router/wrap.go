package router

import "github.com/terminus/actplay/internal/model"

// WrapProcess decorates process metadata for legacy broker adapters.
// Not used on the actplay export hot path.
func WrapProcess(sc model.Scenario) model.Scenario {
	sc.ProcessID = sc.ProcessID + "-wrapped"
	return sc
}
