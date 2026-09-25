use dim_symbol::{ShapeVec, SymbolTable};
use graph_ir::GraphNode;
use std::collections::BTreeMap;

pub fn node_output_shape(
    node: &GraphNode,
    env: &BTreeMap<String, ShapeVec>,
    syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    op_infer::node_rank_infer(node, env, syms)
}
