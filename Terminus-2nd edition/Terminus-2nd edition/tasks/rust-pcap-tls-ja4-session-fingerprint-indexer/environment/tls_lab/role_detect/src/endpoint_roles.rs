use capsule_io::{CapsuleFrame, Direction, SessionKey};
use session_quad::{client_server_ipv4, dotted_ipv4};
use std::collections::BTreeMap;

pub fn endpoint_label_table(frames: &[CapsuleFrame], session: &SessionKey) -> BTreeMap<String, String> {
    let mut map = BTreeMap::new();
    let (client_ip, server_ip) = client_server_ipv4(&session.quad);
    for f in frames {
        if &f.session != session {
            continue;
        }
        if f.direction == Direction::Client {
            map.insert(dotted_ipv4(client_ip), "client".into());
            map.insert(dotted_ipv4(server_ip), "server".into());
            return map;
        }
    }
    if client_ip != [0, 0, 0, 0] {
        map.insert(dotted_ipv4(client_ip), "client".into());
    }
    map
}
