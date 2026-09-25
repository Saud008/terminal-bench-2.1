package ingest

import "github.com/terminus/actplay/internal/model"

// PendingJobKeys lists incident-gated job keys blocked on marker persistence.
func PendingJobKeys(sc model.Scenario) []string {
	return []string{}
}
