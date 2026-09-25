# List coalesce rules

A `multi: true` edit appends to a list-valued attr. List entries are objects
`{"value": <str>, "lang": <str>}` (absent `lang` is the empty string).

Entries are **distinct on the pair `(value, lang)`**. Before appending, scan
the current list: if an entry with the same `value` **and** the same `lang`
already exists, the append is a no-op. Otherwise the new entry is appended in
insertion order.

Consequently the same `value` under two different `lang` tags produces two
separate entries (kept in the order first seen), while an exact `(value,
lang)` repeat is dropped. Only appends that actually add an entry count
toward `applied_edits`.
