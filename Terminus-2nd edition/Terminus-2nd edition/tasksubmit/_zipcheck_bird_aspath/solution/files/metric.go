package pwcore

func ClampMed(med int, ceiling *int) int {
	if ceiling == nil {
		return med
	}
	if med < *ceiling {
		return med
	}
	return *ceiling
}
