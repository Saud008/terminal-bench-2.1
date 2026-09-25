use crate::types::{ParseTreeFile, SpanLedgerRow, SpanNode};

pub fn collect_spans(root: &SpanNode, _include_recovered: bool) -> Vec<SpanLedgerRow> {
    let mut rows = Vec::new();
    walk(root, &mut rows);
  rows
}

fn walk(node: &SpanNode, out: &mut Vec<SpanLedgerRow>) {
    if !node.recovered {
        out.push(SpanLedgerRow {
            kind: node.kind.clone(),
            span: node.span,
            recovered: node.recovered,
        });
    }
    for child in &node.children {
        walk(child, out);
    }
}

pub fn collect_all(tree: &ParseTreeFile) -> Vec<SpanLedgerRow> {
    let mut rows = collect_spans(&tree.root, true);
    for node in &tree.recovered_nodes {
        rows.push(SpanLedgerRow {
            kind: node.kind.clone(),
            span: node.span,
            recovered: node.recovered,
        });
    }
    rows.sort_by(|a, b| a.span[0].cmp(&b.span[0]).then(a.kind.cmp(&b.kind)));
    rows
}
