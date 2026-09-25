# Multipart accounting

Incomplete multipart rows (multipart_complete false and multipart_id set) bill at STANDARD rate for the full window regardless of transitions.

Completed multipart objects bill once at size_bytes. Inventory must not double-count part rows sharing the same multipart_id when multipart_complete is true.

multipart_pending_usd in the cost report sums incomplete MPU bytes only.
