use std::fs;
use std::path::Path;

use crate::PlacedCell;

fn escape_html(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

pub fn write_html(path: &Path, rows: &[Vec<PlacedCell>], _column_count: usize) -> anyhow::Result<()> {
    let mut out = String::from("<table>\n");
    for row in rows {
        out.push_str("  <tr>\n");
        for cell in row {
            let mut attrs = String::new();
            if cell.colspan > 1 {
                attrs.push_str(&format!(" colspan=\"{}\"", cell.colspan));
            }
            if cell.rowspan > 1 {
                attrs.push_str(&format!(" rowspan=\"{}\"", cell.rowspan));
            }
            out.push_str(&format!(
                "    <td{attrs}>{}</td>\n",
                escape_html(&cell.text)
            ));
        }
        out.push_str("  </tr>\n");
    }
    out.push_str("</table>\n");
    fs::write(path, out)?;
    Ok(())
}
