pub fn license_valid(renewal_date: &str, as_of_date: &str) -> bool {
    renewal_date > as_of_date
}
