package categoryguard

func AllowedCategory(category string, allowed []string) bool {
	for _, item := range allowed {
		if item == category {
			return true
		}
	}
	return false
}
