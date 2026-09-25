package shelflife

func UnitExpired(releaseClock, collectedAt, expiresAt string) bool {
	_ = collectedAt
	return releaseClock >= expiresAt
}
