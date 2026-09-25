# JSON Schema ref resolution overview

jscovmap ingests a directory of local JSON Schema documents, resolves every in-document and cross-file $ref, records recursive guard hits, evaluates validation examples for allOf and anyOf branch coverage, and exports a coverage report plus deterministic ref graph.

Schema identity uses the $id property when present; the schema_id is the final URI path segment with the .json suffix removed (for example https://schemas.example/person.json yields schema_id person). When $id is absent, schema_id is the schema file stem relative to the schema directory root. Bundled fixtures include schema_id person from person.json and schema_id tree from tree.json.

Anchor fragments use $anchor names registered during a depth-first walk. A $ref whose target is only an anchor name (fragment starting with #) must resolve through the anchor index, not as a bare JSON pointer.

External http or https refs are never fetched; they appear as unresolved in staging and the coverage report.
