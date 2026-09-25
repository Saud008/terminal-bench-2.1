use graph_ir::GraphDoc;
use init_bind::init_table_load;
use std::collections::BTreeMap;

pub fn initializer_shape_table(doc: &GraphDoc) -> BTreeMap<String, Vec<graph_ir::DimSpec>> {
    init_table_load(doc)
}
