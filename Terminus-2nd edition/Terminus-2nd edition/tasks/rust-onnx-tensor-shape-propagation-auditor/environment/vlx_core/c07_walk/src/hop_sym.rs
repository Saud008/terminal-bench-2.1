use dim_symbol::SymbolTable;
use graph_ir::GraphDoc;

pub fn merge_symbol_links(doc: &GraphDoc) -> SymbolTable {
    let mut syms = SymbolTable::new();
    for pair in &doc.symbol_links {
        if pair.len() == 2 {
            syms.sym_link(&pair[0], &pair[1]);
        }
    }
    syms
}
