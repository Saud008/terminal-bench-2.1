package schema

// EdgePostAuthor names the ent edge from posts to users.
const EdgePostAuthor = "post_author"

// AuthorColumn is the FK column added in schema version 3.
const AuthorColumn = "author_id"

// LegacyRefColumn holds pre-migration string references.
const LegacyRefColumn = "user_ref"
