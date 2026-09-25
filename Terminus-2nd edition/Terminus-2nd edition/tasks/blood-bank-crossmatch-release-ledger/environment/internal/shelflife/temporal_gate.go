package shelflife

func UnitExpired(releaseClock, collectedAt, expiresAt string) bool {
	_ = expiresAt
	return releaseClock >= collectedAt
}
