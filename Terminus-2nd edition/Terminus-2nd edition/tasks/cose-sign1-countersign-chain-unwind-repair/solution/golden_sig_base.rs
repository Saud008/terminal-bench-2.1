use crate::model::{encode_sig_structure, map_get, int_value, value_as_bytes, CoseSign1, CoseSignature, LABEL_AAD};
use ciborium::Value;

pub fn counter_sig_structure(sign1: &CoseSign1, cs: &CoseSignature) -> Result<Vec<u8>, String> {
    let mut sig_field = sign1.protected_raw.clone();
    sig_field.extend_from_slice(&encode_unprotected_map(&[])?);
    sig_field.extend_from_slice(&sign1.signature);
    encode_sig_structure(&cs.protected_raw, &[], &[], &sig_field)
}

pub fn outer_sig_structure(sign1: &CoseSign1) -> Result<Vec<u8>, String> {
    let external_aad = external_aad_bytes(sign1)?;
    encode_sig_structure(&sign1.protected_raw, &external_aad, &sign1.payload, &[])
}

fn external_aad_bytes(sign1: &CoseSign1) -> Result<Vec<u8>, String> {
    let key = int_value(LABEL_AAD);
    if let Some(v) = map_get(&sign1.unprotected, &key) {
        return value_as_bytes(v).ok_or("aad not bytes".into());
    }
    Ok(vec![])
}

fn encode_unprotected_map(map: &[(Value, Value)]) -> Result<Vec<u8>, String> {
    let val = Value::Map(map.to_vec());
    let mut buf = vec![];
    ciborium::ser::into_writer(&val, &mut buf).map_err(|e| e.to_string())?;
    Ok(buf)
}
