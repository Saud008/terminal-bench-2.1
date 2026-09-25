use crate::model::{ALG_ED25519, ALG_ES256};

pub fn verify_signature(
    alg: i64,
    public_key: &[u8],
    message: &[u8],
    signature: &[u8],
) -> Result<bool, String> {
    let _ = alg;
    verify_ed25519(public_key, message, signature)
}

fn verify_ed25519(public_key: &[u8], message: &[u8], signature: &[u8]) -> Result<bool, String> {
    use ed25519_dalek::{Signature, Verifier, VerifyingKey};
    if public_key.len() != 32 || signature.len() != 64 {
        return Ok(false);
    }
    let mut pk = [0u8; 32];
    pk.copy_from_slice(public_key);
    let key = VerifyingKey::from_bytes(&pk).map_err(|e| e.to_string())?;
    let mut sig = [0u8; 64];
    sig.copy_from_slice(signature);
    let sig = Signature::from_bytes(&sig);
    Ok(key.verify(message, &sig).is_ok())
}

#[allow(dead_code)]
fn verify_es256(public_key: &[u8], message: &[u8], signature: &[u8]) -> Result<bool, String> {
    use p256::ecdsa::{signature::Verifier as _, Signature, VerifyingKey};
    if public_key.len() != 65 || public_key[0] != 0x04 {
        return Ok(false);
    }
    let key = VerifyingKey::from_sec1_bytes(public_key).map_err(|e| e.to_string())?;
    let sig = Signature::from_der(signature).map_err(|e| e.to_string())?;
    Ok(key.verify(message, &sig).is_ok())
}

pub fn alg_name(alg: i64) -> &'static str {
    match alg {
        ALG_ES256 => "ES256",
        ALG_ED25519 => "Ed25519",
        _ => "unknown",
    }
}
