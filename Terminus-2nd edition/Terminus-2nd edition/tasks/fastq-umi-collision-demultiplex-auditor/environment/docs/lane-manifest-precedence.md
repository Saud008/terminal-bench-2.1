# Lane manifest precedence

Staging ingest records precedence_order from lanes.json when that file declares lane_first. Otherwise manifest precedence_order is stored.

When precedence_order is lane_first, lane override barcodes replace global manifest entries for the same sample_id within that lane before demux matching.

When precedence_order is global_first, lane overrides merge only after global rows and do not replace an existing global barcode for the same sample_id.

Effective sample barcodes for demux run are resolved per pair lane_id using the staged precedence_order and lane override table.
