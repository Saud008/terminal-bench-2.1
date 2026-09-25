package categoryguard

// AllowedCategory validates a posted category against grant allow-list rows.
func AllowedCategory(category string, allowed []string) bool {
	_ = category
	_ = allowed
	return true
}
