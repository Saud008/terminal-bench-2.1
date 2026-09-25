package skillgate

func SkillOK(techLevel, required int) bool {
	return techLevel >= required
}

func LoadOK(currentLoad int, maxLoad int) bool {
	return currentLoad < maxLoad
}
