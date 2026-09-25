pub mod decoy {
    pub mod decoy_metrics;
}
pub mod headers {
    pub mod hdr_fold;
}
pub mod integrity {
    pub mod ihsh_digest;
}
pub mod norm {
    pub mod url_norm;
}
pub mod pipeline {
    pub mod attestation_emit;
    pub mod attestation_ledger;
}
pub mod policy {
    pub mod mime_guard;
    pub mod scope_guard;
}
pub mod reader {
    pub mod wble_reader;
}
pub mod variants {
    pub mod variant_pick;
}

pub use decoy::decoy_metrics;
pub use headers::hdr_fold;
pub use integrity::ihsh_digest;
pub use norm::url_norm;
pub use pipeline::{attestation_emit, attestation_ledger};
pub use policy::{mime_guard, scope_guard};
pub use reader::wble_reader;
pub use variants::variant_pick;
