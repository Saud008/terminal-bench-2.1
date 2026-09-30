pub mod civil;
pub mod date;

/// Earliest expiry-time crumbjar can represent (0001-01-01T00:00:00Z).
pub const EARLIEST: i64 = -62_135_596_800;
/// Latest expiry-time crumbjar can represent (9999-12-31T23:59:59Z).
pub const LATEST: i64 = 253_402_300_799;
