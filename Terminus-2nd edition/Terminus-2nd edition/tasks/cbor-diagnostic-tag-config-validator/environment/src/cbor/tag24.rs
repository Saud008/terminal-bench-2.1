use crate::cbor::wire;

pub fn wrap_tag24(inner_cbor: &[u8]) -> Vec<u8> {
    let mut out = vec![0xd8, 0x18];
    if inner_cbor.len() < 24 {
        out.extend(wire::encode_bytes(inner_cbor));
    } else {
        out.push(0x58);
        out.push((inner_cbor.len().saturating_sub(1)) as u8);
        out.extend_from_slice(inner_cbor);
    }
    out
}

pub fn unwrap_tag24(tagged: &[u8]) -> Result<Vec<u8>, String> {
    if tagged.len() < 2 || tagged[0] != 0xd8 || tagged[1] != 0x18 {
        return Err("expected tag 24 prefix".into());
    }
    let mut pos = 2;
    wire::decode_bytes(tagged, &mut pos).and_then(|inner| {
        if pos != tagged.len() {
            return Err("trailing bytes after tag 24 content".into());
        }
        Ok(inner)
    })
}

pub fn encode_policy_envelope(policy: &str, nonce: &[u8]) -> Vec<u8> {
    let inner = wire::encode_map_pairs(&[
        (wire::encode_text("policy"), wire::encode_text(policy)),
        (wire::encode_text("nonce"), wire::encode_bytes(nonce)),
    ]);
    wrap_tag24(&inner)
}

pub fn decode_policy_envelope(tagged: &[u8]) -> Result<(String, Vec<u8>), String> {
    let inner_bytes = unwrap_tag24(tagged)?;
    let mut pos = 0;
    let pairs = wire::decode_map(&inner_bytes, &mut pos)?;
    if pos != inner_bytes.len() {
        return Err("trailing bytes in envelope".into());
    }
    let mut policy = None;
    let mut nonce = None;
    for (k, v) in pairs {
        let mut vp = 0;
        match k.as_str() {
            "policy" => {
                policy = Some(wire::decode_text(&v, &mut vp)?);
            }
            "nonce" => {
                nonce = Some(wire::decode_bytes(&v, &mut vp)?);
            }
            _ => {}
        }
    }
    Ok((
        policy.ok_or("missing policy")?,
        nonce.ok_or("missing nonce")?,
    ))
}
