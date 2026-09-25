package migrate

// PlanDown returns rollback phases for reverting schema version 3.
func PlanDown() []phase {
	return []phase{
		"drop_post_author_fk",
		"drop_author_index",
		"drop_author_not_null",
		"drop_author_column",
	}
}
