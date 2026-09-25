# Field norm encoding

Posting norm values in /app/output/segment-stats.json must serialize as JSON numbers in the unsigned 8-bit range (0 through 255) without widening to larger integer types in the exported manifest.

The merge engine stores norms as u8 internally; export must not promote norms to wider integer widths in the stats JSON terms array.
