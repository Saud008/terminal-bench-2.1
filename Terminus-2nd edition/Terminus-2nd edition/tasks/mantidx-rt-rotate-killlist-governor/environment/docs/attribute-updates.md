# Attribute updates

update-attr sets price on docs for the given doc_id.

If the document is killed (killed=1), the update must be rejected:

- attribute-audit.json rejected_killed is true
- price column must not change for killed documents

Killed documents with rejected attribute updates must not become searchable via search union paths.
