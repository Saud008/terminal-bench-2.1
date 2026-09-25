# Tuple schema

Relationship tuples are stored in SQLite at /app/data/relationwatch.db.

## Fields

Each tuple row contains:

- namespace — string namespace prefix (for example doc or audit)
- object — object identifier within the namespace
- relation — relation name on the object
- subject — subject reference; may include transitive tail group:eng#member
- caveat_expr — optional JSON string such as {"allow_subject":"user:bob"}
- created_revision — revision when tuple was written
- tombstone_revision — revision when tuple was deleted; null while active

## Operations

POST /v1/tuple/write accepts operation TOUCH or DELETE.

DELETE sets tombstone_revision to the current head revision without removing the row.

POST /v1/admin/delete-namespace-prefix accepts prefix and tombstones every tuple whose namespace starts with that prefix.

## Transitive example

Tuple doc:plan#viewer@group:eng#member plus doc:group:eng#member@user:alice grants user:alice viewer on doc:plan through group membership expansion handled by internal/closure/cache.go.

## Revision log

Every mutation appends one revision_log row with fields revision, namespace, op, object, relation, subject.
