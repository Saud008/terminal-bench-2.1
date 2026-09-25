pub fn client_server_ipv4(quad: &[u8; 8]) -> ([u8; 4], [u8; 4]) {
    let client = [quad[0], quad[1], quad[2], quad[3]];
    let server = [quad[4], quad[5], quad[6], quad[7]];
    (client, server)
}

pub fn dotted_ipv4(oct: [u8; 4]) -> String {
    format!("{}.{}.{}.{}", oct[0], oct[1], oct[2], oct[3])
}

pub fn format_session_id(quad: &[u8; 8]) -> String {
    quad.iter().map(|b| format!("{b:02x}")).collect()
}
