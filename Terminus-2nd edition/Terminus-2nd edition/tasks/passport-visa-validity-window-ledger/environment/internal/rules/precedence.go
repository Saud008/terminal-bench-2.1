package rules

import "github.com/terminus/borderdocctl/internal/model"

// EffectiveMaxStay picks the applicable max_stay cap for a port.
func EffectiveMaxStay(portCode string, ruleRows []model.Rule) int {
	federal := 0
	portCap := 0
	for _, r := range ruleRows {
		switch r.Scope {
		case "federal":
			if r.MaxStayDays > federal {
				federal = r.MaxStayDays
			}
		case "port":
			if r.PortCode == portCode && r.MaxStayDays > portCap {
				portCap = r.MaxStayDays
			}
		}
	}
	if portCap > 0 {
		return portCap
	}
	return federal
}
