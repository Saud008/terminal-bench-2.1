use ciborium::Value;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const LABEL_ALG: i64 = 1;
pub const LABEL_KID: i64 = 2;
pub const LABEL_AAD: i64 = 3;
pub const LABEL_COUNTERSIGN: i64 = 11;

pub const ALG_ES256: i64 = -7;
pub const ALG_ED25519: i64 = -8;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustPayload {
    pub message: String,
    pub anchors: BTreeMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct CoseSign1 {
    pub protected_raw: Vec<u8>,
    pub protected: BTreeMap<i64, Value>,
    pub unprotected: Vec<(Value, Value)>,
    pub payload: Vec<u8>,
    pub signature: Vec<u8>,
    pub countersigns: Vec<CoseSignature>,
}

#[derive(Debug, Clone)]
pub struct CoseSignature {
    pub protected_raw: Vec<u8>,
    pub protected: BTreeMap<i64, Value>,
    pub unprotected: Vec<(Value, Value)>,
    pub signature: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnwindStep {
    pub index: usize,
    pub kid: String,
    pub alg: i64,
    pub verify_ok: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChainResult {
    pub input_sha256: String,
    pub outer_ok: bool,
    pub countersign_ok: bool,
    pub partial_retained: bool,
    pub unwind: Vec<UnwindStep>,
}

pub fn int_value(v: i64) -> Value {
    Value::Integer(v.into())
}

pub fn map_get<'a>(map: &'a [(Value, Value)], key: &Value) -> Option<&'a Value> {
    map.iter().find(|(k, _)| k == key).map(|(_, v)| v)
}

pub fn value_as_i64(v: &Value) -> Option<i64> {
    match v {
        Value::Integer(i) => i64::try_from(*i).ok(),
        _ => None,
    }
}

pub fn value_as_bytes(v: &Value) -> Option<Vec<u8>> {
    match v {
        Value::Bytes(b) => Some(b.clone()),
        Value::Text(s) => Some(s.as_bytes().to_vec()),
        _ => None,
    }
}

pub fn value_as_text(v: &Value) -> Option<String> {
    match v {
        Value::Text(s) => Some(s.clone()),
        _ => None,
    }
}

pub fn parse_protected(raw: &[u8]) -> Result<BTreeMap<i64, Value>, String> {
    let val: Value = ciborium::de::from_reader(raw).map_err(|e| e.to_string())?;
    let map = match val {
        Value::Map(m) => m,
        _ => return Err("protected not map".into()),
    };
    let mut out = BTreeMap::new();
    for (k, v) in map {
        let key = match k {
            Value::Integer(i) => i64::try_from(i).map_err(|_| "bad key")?,
            _ => return Err("protected key not int".into()),
        };
        out.insert(key, v);
    }
    Ok(out)
}

pub fn trust_from_payload(payload: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, String> {
    let tp: TrustPayload =
        serde_json::from_slice(payload).map_err(|e| format!("payload json: {e}"))?;
    let mut anchors = BTreeMap::new();
    for (kid, hexpk) in tp.anchors {
        let pk = hex::decode(hexpk).map_err(|e| format!("anchor hex: {e}"))?;
        anchors.insert(kid, pk);
    }
    Ok(anchors)
}

pub fn parse_sign1(bytes: &[u8]) -> Result<CoseSign1, String> {
    let val: Value = ciborium::de::from_reader(bytes).map_err(|e| e.to_string())?;
    let arr = match val {
        Value::Array(a) if a.len() == 4 => a,
        _ => return Err("sign1 not 4-array".into()),
    };
    let protected_raw = value_as_bytes(&arr[0]).ok_or("protected not bytes")?;
    let protected = parse_protected(&protected_raw)?;
    let unprotected = map_from_value(&arr[1])?;
    let payload = value_as_bytes(&arr[2]).unwrap_or_default();
    let signature = value_as_bytes(&arr[3]).ok_or("signature not bytes")?;
    let countersigns = extract_countersigns(&unprotected)?;
    Ok(CoseSign1 {
        protected_raw,
        protected,
        unprotected,
        payload,
        signature,
        countersigns,
    })
}

fn map_from_value(v: &Value) -> Result<Vec<(Value, Value)>, String> {
    match v {
        Value::Map(m) => Ok(m.clone()),
        Value::Null => Ok(vec![]),
        _ => Err("expected map".into()),
    }
}

fn extract_countersigns(unprot: &[(Value, Value)]) -> Result<Vec<CoseSignature>, String> {
    let key = int_value(LABEL_COUNTERSIGN);
    let Some(Value::Array(items)) = map_get(unprot, &key) else {
        return Ok(vec![]);
    };
    let mut out = vec![];
    for item in items {
        let arr = match item {
            Value::Array(a) if a.len() == 3 => a,
            _ => return Err("countersign not 3-array".into()),
        };
        let protected_raw = value_as_bytes(&arr[0]).ok_or("cs protected not bytes")?;
        let protected = parse_protected(&protected_raw)?;
        let unprotected = map_from_value(&arr[1])?;
        let signature = value_as_bytes(&arr[2]).ok_or("cs signature not bytes")?;
        out.push(CoseSignature {
            protected_raw,
            protected,
            unprotected,
            signature,
        });
    }
    Ok(out)
}

pub fn encode_sig_structure(
    protected: &[u8],
    external_aad: &[u8],
    payload: &[u8],
    sig_bytes: &[u8],
) -> Result<Vec<u8>, String> {
    let arr = Value::Array(vec![
        Value::Text("Signature1".into()),
        Value::Bytes(protected.to_vec()),
        Value::Bytes(external_aad.to_vec()),
        Value::Bytes(payload.to_vec()),
        Value::Bytes(sig_bytes.to_vec()),
    ]);
    let mut buf = vec![];
    ciborium::ser::into_writer(&arr, &mut buf).map_err(|e| e.to_string())?;
    Ok(buf)
}
