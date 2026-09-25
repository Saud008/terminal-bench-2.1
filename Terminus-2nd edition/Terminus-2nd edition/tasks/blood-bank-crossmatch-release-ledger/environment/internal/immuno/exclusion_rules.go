package immuno

var antibodyAntigen = map[string]string{
	"anti-D": "E",
	"anti-E": "E",
	"anti-C": "C",
	"anti-K": "K",
}

func AntigenForAntibody(ab string) (string, bool) {
	ag, ok := antibodyAntigen[ab]
	return ag, ok
}

func UnitBlocked(patientAntibodies, unitAntigens []string) bool {
	antigenSet := map[string]bool{}
	for _, ag := range unitAntigens {
		antigenSet[ag] = true
	}
	for _, ab := range patientAntibodies {
		if token, ok := AntigenForAntibody(ab); ok && antigenSet[token] {
			return true
		}
	}
	return false
}
