use crate::attest_model::PolicyFile;

pub fn uv_satisfied(policy: &PolicyFile, uv: bool) -> bool {
    match policy.user_verification.as_str() {
        "discouraged" => uv,
        "preferred" => true,
        "required" => uv,
        _ => false,
    }
}
