use crate::attest_model::CertLink;

pub fn chain_valid(links: &[CertLink]) -> bool {
    if links.is_empty() {
        return false;
    }
    for link in links {
        if link.role == "root" && link.subject_fp != link.issuer_fp {
            return false;
        }
    }
    for pair in links.windows(2) {
        if pair[0].issuer_fp != pair[1].subject_fp {
            return false;
        }
    }
    true
}
