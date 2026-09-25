# OFS delta window

ofs_delta entries reference a base object by base_pack_offset matching the base entry pack_offset in staging.

Copy offsets in patch scripts are measured from the start of the resolved base inflated bytes (pre-image window origin). Using the post-patch tail of the base object or shifting the window by compressed patch length is incorrect.

The base window is the full inflated base payload before any dependent patch runs.
