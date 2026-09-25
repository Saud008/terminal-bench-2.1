use crate::mw11::InfeasRow;

pub fn record_infeasible(job_id: &str, reason: &str, out: &mut Vec<InfeasRow>) {
    out.push(InfeasRow {
        job_id: job_id.to_string(),
        reason: reason.to_string(),
    });
}
