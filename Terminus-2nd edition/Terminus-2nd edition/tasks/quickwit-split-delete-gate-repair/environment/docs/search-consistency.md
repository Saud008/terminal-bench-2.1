# Search consistency

Search tokenizes body text on whitespace, lowercases tokens, and matches whole tokens.

Hit count is the number of distinct doc_id values whose body contains the query token and that are not tombstoned when delete-audit tombstones_applied is true.

After index, delete, merge, and search in one session, hit counts must reflect merged postings minus tombstoned documents.

search-report.json and search-export.json use the same schema: query string, hit_count integer, doc_ids array sorted ascending.

When TB3_DOCS_DIR points at an absolute fixture directory, index loads batches from that directory identically to /app/fixtures/docs/.
