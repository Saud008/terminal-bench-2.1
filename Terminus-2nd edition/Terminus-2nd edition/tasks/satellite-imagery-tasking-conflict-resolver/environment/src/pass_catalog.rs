use crate::tasking_types::PassWindow;
use std::collections::BTreeMap;

pub fn pass_index(windows: &[PassWindow]) -> BTreeMap<String, PassWindow> {
    windows.iter().map(|p| (p.pass_id.clone(), p.clone())).collect()
}
