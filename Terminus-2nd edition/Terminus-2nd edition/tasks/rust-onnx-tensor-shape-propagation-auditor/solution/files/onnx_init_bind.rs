use graph_ir::{GraphDoc, TensorPort};
use std::collections::BTreeMap;

pub fn init_table_load(doc: &GraphDoc) -> BTreeMap<String, Vec<graph_ir::DimSpec>> {
    let mut table = BTreeMap::new();
    for init in &doc.initializers {
        table.insert(init.name.clone(), init.shape.clone());
    }
    for vi in &doc.value_infos {
        if table.contains_key(&vi.name) {
            continue;
        }
        if let Some(shape) = &vi.shape {
            table.insert(vi.name.clone(), shape.clone());
        }
    }
    table
}
