package migrate

type phase string

const (
	phaseCodegen      phase = "codegen_refresh"
	phaseSnapshot     phase = "atlas_snapshot"
	phasePreValidate  phase = "ent_pre_validate"
	phaseAddColumn    phase = "add_author_nullable"
	phaseBackfill     phase = "backfill_author"
	phasePostValidate phase = "ent_post_validate"
	phaseNotNull      phase = "set_author_not_null"
	phaseAddFK        phase = "add_post_author_fk"
	phaseAddIndex     phase = "add_author_index"
)
