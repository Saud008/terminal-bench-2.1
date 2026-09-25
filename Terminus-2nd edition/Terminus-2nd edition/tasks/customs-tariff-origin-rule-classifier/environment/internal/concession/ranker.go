package concession
import "sort"
type Rule struct {
	AgreementCode string
	HSPrefix      string
	RVCMinBPS     int64
	DutyRateBPS   int64
	Priority      int
}
func PickAgreement(hsNorm string, rules []Rule) *Rule {
	var matches []Rule
	for _, r := range rules {
		if len(r.HSPrefix) <= len(hsNorm) && hsNorm[:len(r.HSPrefix)] == r.HSPrefix {
			matches = append(matches, r)
		}
	}
	if len(matches) == 0 {
		return nil
	}
	sort.Slice(matches, func(i, j int) bool {
		if matches[i].Priority == matches[j].Priority {
			return matches[i].AgreementCode > matches[j].AgreementCode
		}
		return matches[i].Priority > matches[j].Priority
	})
	return &matches[0]
}
