package seal

// MaybeRevokeBan — SHIPPING BROKEN: no-op (grace window never deactivates ban).
func (m *Manager) MaybeRevokeBan(breachID int64, nowMonoMs int64) error {
	_ = breachID
	_ = nowMonoMs
	_ = m.GraceMs
	return nil
}
