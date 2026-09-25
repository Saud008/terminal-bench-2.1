# Archive bundle format

A bundle file is a concatenation of independent gzip members. Each member contains UTF-8 JSONL with one archived task record per line.

Task record fields:

id — string task identifier
queue — queue name string
payload — opaque string body
retry — integer retry count at archive time
max_retry — integer max retry budget
priority — integer queue priority (lower runs sooner)
archived_at_ms — UTC epoch milliseconds when archived

Member boundaries must end with a complete gzip footer (ISIZE and CRC). Readers must reject members whose recorded compressed size in the index does not include the footer bytes.

The companion index sidecar lists members with file_offset, compressed_size, and task_ids in member order.
