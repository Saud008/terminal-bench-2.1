use serde::Serialize;
use serde_json::Value;

use crate::error::{DecodeError, LimitKind};
use crate::model::DecodedValue;

#[derive(Debug, Clone, Serialize)]
pub struct DecodeReport {
    pub status: &'static str,
    pub error_code: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit_kind: Option<LimitKind>,
    pub value: Option<Value>,
    pub bytes_consumed: u64,
}

impl DecodeReport {
    pub fn ok(value: DecodedValue, bytes_consumed: u64) -> Self {
        Self {
            status: "ok",
            error_code: None,
            limit_kind: None,
            value: Some(value.to_json()),
            bytes_consumed,
        }
    }

    pub fn error(err: DecodeError, bytes_consumed: u64, _max_bytes: u64) -> Self {
        Self {
            status: "error",
            error_code: Some(err.code()),
            limit_kind: err.limit_kind(),
            value: None,
            bytes_consumed,
        }
    }
}
