package hemcompat

var aboReceive = map[string]map[string]bool{
	"O":  {"O": true},
	"A":  {"A": true, "O": true},
	"B":  {"B": true, "O": true},
	"AB": {"A": true, "B": true, "AB": true, "O": true},
}

func ABOCompatible(patientABO, unitABO string) bool {
	allowed, ok := aboReceive[patientABO]
	if !ok {
		return false
	}
	return allowed[unitABO]
}

func RhCompatible(patientRh, unitRh string) bool {
	if patientRh == "neg" {
		return true
	}
	return patientRh == unitRh || unitRh == "pos" || unitRh == "neg"
}
