use ja4_canon::HandshakeView;

pub fn parse_handshake_view(bytes: &[u8]) -> HandshakeView {
    let body = first_client_hello_body(bytes);
    let mut tls_version = 0x0303u16;
    let mut ciphers = Vec::new();
    let mut extensions = Vec::new();
    let mut alpn = String::new();
    if body.len() < 6 {
        return HandshakeView {
            tls_version,
            cipher_suites: ciphers,
            extensions,
            alpn,
        };
    }
    tls_version = u16::from_be_bytes([body[4], body[5]]);
    let mut off = 38usize;
    if off >= body.len() {
        return HandshakeView {
            tls_version,
            cipher_suites: ciphers,
            extensions,
            alpn,
        };
    }
    let sid_len = body[off] as usize;
    off += 1 + sid_len;
    if off + 2 > body.len() {
        return HandshakeView {
            tls_version,
            cipher_suites: ciphers,
            extensions,
            alpn,
        };
    }
    let cs_len = u16::from_be_bytes([body[off], body[off + 1]]) as usize;
    off += 2;
    for _ in 0..(cs_len / 2) {
        if off + 2 > body.len() {
            break;
        }
        ciphers.push(u16::from_be_bytes([body[off], body[off + 1]]));
        off += 2;
    }
    if off + 2 <= body.len() {
        let ext_len = u16::from_be_bytes([body[off], body[off + 1]]) as usize;
        off += 2;
        let ext_end = off + ext_len;
        while off + 4 <= ext_end && off + 4 <= body.len() {
            let etype = u16::from_be_bytes([body[off], body[off + 1]]);
            let elen = u16::from_be_bytes([body[off + 2], body[off + 3]]) as usize;
            extensions.push(etype);
            if etype == 0x10 && off + 4 + elen <= body.len() {
                let data = &body[off + 4..off + 4 + elen];
                if !data.is_empty() {
                    let slen = data[0] as usize;
                    if data.len() >= 1 + slen {
                        alpn = String::from_utf8_lossy(&data[1..1 + slen]).into_owned();
                    }
                }
            }
            off += 4 + elen;
        }
    }
    HandshakeView {
        tls_version,
        cipher_suites: ciphers,
        extensions,
        alpn,
    }
}

fn first_client_hello_body(buf: &[u8]) -> &[u8] {
    let mut off = 0usize;
    while off + 5 <= buf.len() {
        let ctype = buf[off];
        let len = u16::from_be_bytes([buf[off + 3], buf[off + 4]]) as usize;
        if off + 5 + len > buf.len() {
            break;
        }
        let body = &buf[off + 5..off + 5 + len];
        if ctype == 0x16 && !body.is_empty() && body[0] == 0x01 {
            return body;
        }
        off += 5 + len;
    }
    buf
}
