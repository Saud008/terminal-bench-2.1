package migrate

// PlanUp returns the ordered up-migration phases for the post_author edge.
func PlanUp() []phase {
	return []phase{
		phaseSnapshot,
		phaseCodegen,
		phasePreValidate,
		phaseAddColumn,
		phaseAddFK,
		phaseBackfill,
		phaseNotNull,
		phasePostValidate,
		phaseAddIndex,
	}
}
