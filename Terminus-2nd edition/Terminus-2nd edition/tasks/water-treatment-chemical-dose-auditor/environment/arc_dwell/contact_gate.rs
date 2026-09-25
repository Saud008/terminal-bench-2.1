pub fn minute_eligible(flow_lpm: f64, min_flow_lpm: f64) -> bool {
    flow_lpm < min_flow_lpm
}
