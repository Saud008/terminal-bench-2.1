package seal

func (m *Manager) MaybeRevokeBan(breachID int64, nowMonoMs int64) error {
	opened, err := m.Store.BreachOpenedMono(breachID)
	if err != nil {
		return err
	}
	if nowMonoMs-opened <= m.GraceMs {
		return m.Store.DeactivateBan(breachID)
	}
	return nil
}
