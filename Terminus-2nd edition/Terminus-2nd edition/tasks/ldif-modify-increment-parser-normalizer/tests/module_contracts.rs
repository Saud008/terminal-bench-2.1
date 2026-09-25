use ldif_core::apply::apply_records;
use ldif_core::model::{ChangeRecord, ModifyKind, ModifyOp};
use ldif_core::parser::{decode_value, unfold_lines};
fn attrs(pairs: &[(&str, Vec<&str>)]) -> std::collections::BTreeMap<String, Vec<String>> {
    pairs
        .iter()
        .map(|(k, v)| (k.to_string(), v.iter().map(|s| s.to_string()).collect()))
        .collect()
}

fn modify_op(kind: ModifyKind, attr: &str, values: Vec<&str>) -> ModifyOp {
    ModifyOp {
        kind,
        attr: attr.into(),
        values: values.into_iter().map(str::to_string).collect(),
    }
}

#[test]
fn parser_unfolds_continuation_lines() {
    let raw = "description: alpha beta \n delta gamma\n";
    let lines = unfold_lines(raw);
    assert_eq!(lines.len(), 1);
    assert_eq!(lines[0], "description: alpha beta delta gamma");
}

#[test]
fn parser_decodes_unpadded_base64() {
    let value = decode_value(true, "c2VjcmV0LXRva2Vu").expect("decode");
    assert_eq!(value, "secret-token");
}

#[test]
fn apply_modify_respects_file_order() {
    let bootstrap = ChangeRecord::add(
        "cn=Test,dc=example,dc=com",
        attrs(&[(
            "mail",
            vec!["keep@example.com", "drop@example.com"],
        )]),
    );
    let modify = ChangeRecord::modify(
        "cn=Test,dc=example,dc=com",
        vec![
            modify_op(ModifyKind::Add, "mail", vec!["new@example.com"]),
            modify_op(ModifyKind::Delete, "mail", vec!["drop@example.com"]),
        ],
    );
    let (export, _) = apply_records("test", &[bootstrap, modify]).expect("apply");
    let entry = &export.entries[0];
    let mail = entry.attributes.get("mail").expect("mail");
    assert!(mail.contains(&"keep@example.com".to_string()));
    assert!(mail.contains(&"new@example.com".to_string()));
    assert!(!mail.contains(&"drop@example.com".to_string()));
}

#[test]
fn apply_delete_value_vs_attribute() {
    let bootstrap = ChangeRecord::add(
        "cn=Test,dc=example,dc=com",
        attrs(&[
            ("mail", vec!["one@example.com", "two@example.com"]),
            ("title", vec!["Engineer"]),
        ]),
    );
    let modify = ChangeRecord::modify(
        "cn=Test,dc=example,dc=com",
        vec![
            modify_op(ModifyKind::Delete, "mail", vec!["two@example.com"]),
            modify_op(ModifyKind::Delete, "title", vec![]),
        ],
    );
    let (export, _) = apply_records("test", &[bootstrap, modify]).expect("apply");
    let entry = &export.entries[0];
    assert_eq!(
        entry.attributes.get("mail").cloned(),
        Some(vec!["one@example.com".to_string()])
    );
    assert!(!entry.attributes.contains_key("title"));
}

#[test]
fn apply_add_replaces_existing_dn() {
    let first = ChangeRecord::add(
        "cn=User,dc=example,dc=com",
        attrs(&[
            ("cn", vec!["Old"]),
            ("description", vec!["stale"]),
        ]),
    );
    let second = ChangeRecord::add(
        "cn=User,dc=example,dc=com",
        attrs(&[
            ("cn", vec!["New"]),
            ("mail", vec!["user@example.com"]),
        ]),
    );
    let (export, _) = apply_records("test", &[first, second]).expect("apply");
    let entry = &export.entries[0];
    assert_eq!(
        entry.attributes.get("cn").cloned(),
        Some(vec!["New".to_string()])
    );
    assert!(!entry.attributes.contains_key("description"));
    assert_eq!(
        entry.attributes.get("mail").cloned(),
        Some(vec!["user@example.com".to_string()])
    );
}

#[test]
fn apply_merges_attribute_case() {
    let record = ChangeRecord::add(
        "cn=Case,dc=example,dc=com",
        attrs(&[
            ("mail", vec!["lower@example.com"]),
            ("Mail", vec!["upper@example.com"]),
        ]),
    );
    let (export, _) = apply_records("test", &[record]).expect("apply");
    let mail = export.entries[0].attributes.get("mail").expect("mail");
    assert_eq!(mail.len(), 2);
    assert!(mail.contains(&"lower@example.com".to_string()));
    assert!(mail.contains(&"upper@example.com".to_string()));
}
