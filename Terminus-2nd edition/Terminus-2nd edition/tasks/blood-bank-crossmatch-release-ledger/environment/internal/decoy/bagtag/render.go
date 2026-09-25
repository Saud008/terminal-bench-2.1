package bagtag

import "fmt"

func BarcodeLabel(unitID, abo, rh string) string {
	return fmt.Sprintf("BB-%s-%s%s", unitID, abo, rh)
}

func DisplayRh(rh string) string {
	if rh == "pos" {
		return "+"
	}
	return "-"
}
