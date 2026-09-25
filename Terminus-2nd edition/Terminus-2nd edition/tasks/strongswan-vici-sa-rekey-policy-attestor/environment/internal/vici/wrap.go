package vici

// WrapEvent decorates VICI event type strings for logging (decoy helper).
func WrapEvent(typ string) string {
	return "vici:" + typ
}
