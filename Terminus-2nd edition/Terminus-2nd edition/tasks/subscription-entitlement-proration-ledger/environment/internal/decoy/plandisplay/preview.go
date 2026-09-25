package plandisplay

import "fmt"

// PreviewPlan renders catalog text for operators; not used on billing hot path.
func PreviewPlan(planID string, monthlyCents int64) string {
    return fmt.Sprintf("plan %s monthly=%d", planID, monthlyCents)
}
