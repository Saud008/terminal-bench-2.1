# allOf and anyOf coverage

For each validation example line, jscovmap walks the root schema of the named schema_id and records which combinator branches the instance satisfies.

allOf branch i is covered when the instance matches branch i under the type and const rules in combinator_coverage.rs.

anyOf branch i is covered only when that specific branch matches the instance. Marking every anyOf sibling because one branch matched is incorrect.

Branch paths use the JSON pointer prefix to the combinator, for example /allOf/0 or /allOf/1/anyOf/0 when anyOf is nested under an allOf branch.
