use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use ed25519_dalek::{Signer, SigningKey};
use sha2::{Digest, Sha256};
use witness_ledger::types::{KeyEntry, PolicyDoc, RevocationRow, WitnessRow};

fn canonical_message(
    release_id: &str,
    artifact_digest: &str,
    epoch: u64,
    prior_witness_id: Option<&str>,
) -> Vec<u8> {
    let prior = prior_witness_id.unwrap_or("none");
    let body = format!(
        "TW1\nartifact_digest={artifact_digest}\nepoch={epoch}\nprior_witness_id={prior}\nrelease_id={release_id}\n"
    );
    body.into_bytes()
}

fn signing_key(seed_byte: u8) -> SigningKey {
    let seed = [seed_byte; 32];
    SigningKey::from_bytes(&seed)
}

fn artifact_digest(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("sha256:{}", hex::encode(hasher.finalize()))
}

fn write_bundle(
    dest: &Path,
    release_id: &str,
    threshold: u32,
    total: u32,
    artifact_name: &str,
    artifact_bytes: &[u8],
    keys: &BTreeMap<String, KeyEntry>,
    signers: &BTreeMap<String, SigningKey>,
    revocations: &[RevocationRow],
    witness_specs: &[(&str, &str, u64, Option<&str>)],
) {
    fs::create_dir_all(dest.join("artifacts")).unwrap();
    fs::create_dir_all(dest.join("witnesses")).unwrap();
    let art_path = dest.join("artifacts").join(artifact_name);
    fs::write(&art_path, artifact_bytes).unwrap();
    let digest = artifact_digest(artifact_bytes);

    let policy = PolicyDoc {
        release_id: release_id.to_string(),
        quorum: witness_ledger::types::QuorumSpec { threshold, total },
        artifact_file: format!("artifacts/{artifact_name}"),
    };
    fs::write(
        dest.join("policy.json"),
        serde_json::to_string_pretty(&policy).unwrap() + "\n",
    )
    .unwrap();
    fs::write(
        dest.join("keys.json"),
        serde_json::to_string_pretty(keys).unwrap() + "\n",
    )
    .unwrap();
    let rev_text: String = revocations
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect::<Vec<_>>()
        .join("\n");
    if !rev_text.is_empty() {
        fs::write(dest.join("revocations.jsonl"), rev_text + "\n").unwrap();
    } else {
        fs::write(dest.join("revocations.jsonl"), "").unwrap();
    }

    for (wid, kid, epoch, prior) in witness_specs {
        let msg = canonical_message(release_id, &digest, *epoch, *prior);
        let sig = signers.get(*kid).unwrap().sign(&msg);
        let row = WitnessRow {
            witness_id: wid.to_string(),
            release_id: release_id.to_string(),
            artifact_digest: digest.clone(),
            epoch: *epoch,
            prior_witness_id: prior.map(|s| s.to_string()),
            signer_keyid: kid.to_string(),
            signature: hex::encode(sig.to_bytes()),
        };
        fs::write(
            dest.join("witnesses").join(format!("{wid}.json")),
            serde_json::to_string_pretty(&row).unwrap() + "\n",
        )
        .unwrap();
    }
}

fn key_entry(kid: &str, sk: &SigningKey) -> KeyEntry {
    KeyEntry {
        keyid: kid.to_string(),
        scheme: "ed25519".to_string(),
        public: hex::encode(sk.verifying_key().to_bytes()),
    }
}

fn main() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let bundles = root.join("data/bundles/release-alpha");
    let tb3 = root.join("verifier-fixtures/tb3-bundle");
    let edge = root.join("verifier-fixtures/revoke-edge-bundle");

    let mut alpha_signers = BTreeMap::new();
    alpha_signers.insert("key-a".to_string(), signing_key(0x11));
    alpha_signers.insert("key-b".to_string(), signing_key(0x22));
    alpha_signers.insert("key-c".to_string(), signing_key(0x33));
    alpha_signers.insert("key-d".to_string(), signing_key(0x44));
    let alpha_keys: BTreeMap<String, KeyEntry> = alpha_signers
        .iter()
        .map(|(k, sk)| (k.clone(), key_entry(k, sk)))
        .collect();
    write_bundle(
        &bundles,
        "app-v2.4.0",
        2,
        4,
        "release.pkg",
        b"RELEASE-ALPHA-PAYLOAD-v2\n",
        &alpha_keys,
        &alpha_signers,
        &[RevocationRow {
            keyid: "key-c".to_string(),
            revoked_epoch: 50,
        }],
        &[
            ("w001", "key-a", 10, None),
            ("w002", "key-b", 20, Some("w001")),
            ("w003", "key-c", 40, Some("w002")),
            ("w004", "key-b", 15, Some("w001")),
        ],
    );

    let mut tb3_signers = BTreeMap::new();
    tb3_signers.insert("tb3-a".to_string(), signing_key(0xaa));
    tb3_signers.insert("tb3-b".to_string(), signing_key(0xbb));
    tb3_signers.insert("tb3-c".to_string(), signing_key(0xcc));
    let tb3_keys: BTreeMap<String, KeyEntry> = tb3_signers
        .iter()
        .map(|(k, sk)| (k.clone(), key_entry(k, sk)))
        .collect();
    write_bundle(
        &tb3,
        "svc-v9.1",
        2,
        3,
        "service.pkg",
        b"TB3-HIDDEN-RELEASE-BIN\n",
        &tb3_keys,
        &tb3_signers,
        &[RevocationRow {
            keyid: "tb3-c".to_string(),
            revoked_epoch: 37,
        }],
        &[
            ("tw01", "tb3-a", 30, None),
            ("tw02", "tb3-b", 35, Some("tw01")),
            ("tw03", "tb3-c", 36, Some("tw01")),
        ],
    );

    let mut edge_signers = BTreeMap::new();
    edge_signers.insert("edge-a".to_string(), signing_key(0xde));
    edge_signers.insert("edge-b".to_string(), signing_key(0xed));
    let edge_keys: BTreeMap<String, KeyEntry> = edge_signers
        .iter()
        .map(|(k, sk)| (k.clone(), key_entry(k, sk)))
        .collect();
    write_bundle(
        &edge,
        "edge-rel",
        2,
        2,
        "edge.pkg",
        b"EDGE-REVOKE-CASE\n",
        &edge_keys,
        &edge_signers,
        &[RevocationRow {
            keyid: "edge-a".to_string(),
            revoked_epoch: 100,
        }],
        &[
            ("e001", "edge-a", 99, None),
            ("e002", "edge-b", 100, Some("e001")),
        ],
    );

    println!("gen-fixtures: wrote bundles");
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let vf = Path::new("/opt/verifier-fixtures/witness-bundles");
    let _ = std::fs::remove_dir_all(vf);
    let _ = std::fs::create_dir_all(vf);
    copy_dir_all(&root.join("verifier-fixtures/tb3-bundle"), &vf.join("tb3-bundle"));
    copy_dir_all(
        &root.join("verifier-fixtures/revoke-edge-bundle"),
        &vf.join("revoke-edge-bundle"),
    );
}

fn copy_dir_all(src: &Path, dst: &Path) {
    std::fs::create_dir_all(dst).unwrap();
    for entry in std::fs::read_dir(src).unwrap() {
        let entry = entry.unwrap();
        let ty = entry.file_type().unwrap();
        let dest = dst.join(entry.file_name());
        if ty.is_dir() {
            copy_dir_all(&entry.path(), &dest);
        } else {
            std::fs::copy(entry.path(), dest).unwrap();
        }
    }
}
