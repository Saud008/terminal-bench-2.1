# LDIF files we feed ldif-apply

Each apply run ingests one change log and transforms the in-memory directory before export.

Change logs are plain text. Records are separated by one or more blank lines.

Each record starts with dn: and changetype: (add, modify, or delete). Add and delete records list attributes as name/value lines. Modify records contain operation blocks: each block begins with add:, delete:, or replace: plus an attribute name, then optional attr: value lines for that attribute. A line that is only - separates blocks. Operations within one modify record are applied in file order. Do not reorder by operation kind.

Line folding: if a physical line begins with one space, it continues the previous line. The space itself is not kept when joining.

Attribute syntax uses either one colon (plain text value) or two colons (base64 payload after the name).

Some fixtures under /app/fixtures/ldif/ use {{SEED:label}} in mail values. Replace those with a per-seed token when you run apply locally; see /app/fixtures/seeds.json for seed ids we use in examples.
