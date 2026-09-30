//! Two-column report: labels right-aligned to the widest label, one space,
//! then the value. No trailing padding.

pub struct Table {
    rows: Vec<(String, String)>,
}

impl Table {
    pub fn new() -> Table {
        Table { rows: Vec::new() }
    }

    pub fn add(&mut self, label: &str, value: &str) {
        self.rows.push((label.to_string(), value.to_string()));
    }

    pub fn render(&self) -> String {
        let width = self.rows.iter().map(|(l, _)| l.chars().count()).max().unwrap_or(0);
        let mut out = String::new();
        for (label, value) in &self.rows {
            out.push_str(&format!("{:>w$} {}\n", label, value, w = width));
        }
        out
    }
}
