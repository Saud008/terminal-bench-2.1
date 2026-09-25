package migrate

// PlanUp returns the ordered up-migration phases for the post_author edge.
func PlanUp() []phase {
	return []phase{
		phaseCodegen,
		phaseSnapshot,
		phasePreValidate,
		phaseAddColumn,
		phaseBackfill,
		phasePostValidate,
		phaseNotNull,
		phaseAddFK,
		phaseAddIndex,
	}
}
