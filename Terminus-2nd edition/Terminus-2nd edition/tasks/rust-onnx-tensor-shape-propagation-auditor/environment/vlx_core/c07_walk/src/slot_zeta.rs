use dim_symbol::{parse_dim_specs, DimVal, ShapeVec};
use graph_ir::GraphDoc;
use std::collections::BTreeMap;

use crate::hop_init::initializer_shape_table;
use crate::hop_node::node_output_shape;
use crate::hop_port::port_dim_specs;
use crate::hop_sym::merge_symbol_links;

#[derive(Debug, Clone)]
pub struct PropagatedTensor {
    pub graph_id: String,
    pub tensor: String,
    pub shape: ShapeVec,
    pub node_id: String,
    pub ordinal: u32,
}

pub fn propagate_graph(doc: &GraphDoc) -> Result<Vec<PropagatedTensor>, String> {
    let syms = merge_symbol_links(doc);
    let init_table = initializer_shape_table(doc);
    let mut env: BTreeMap<String, ShapeVec> = BTreeMap::new();
    let mut ordinal = 0u32;
    let mut rows = Vec::new();
    for inp in &doc.inputs {
        let specs = port_dim_specs(inp);
        let shape = parse_dim_specs(&specs);
        env.insert(inp.name.clone(), shape.clone());
        rows.push(PropagatedTensor {
            graph_id: doc.graph_id.clone(),
            tensor: inp.name.clone(),
            shape,
            node_id: "input".into(),
            ordinal,
        });
        ordinal += 1;
    }
    for init in &doc.initializers {
        if let Some(specs) = init_table.get(&init.name) {
            let shape = parse_dim_specs(specs);
            env.insert(init.name.clone(), shape.clone());
            rows.push(PropagatedTensor {
                graph_id: doc.graph_id.clone(),
                tensor: init.name.clone(),
                shape,
                node_id: "initializer".into(),
                ordinal,
            });
            ordinal += 1;
        }
    }
    for node in &doc.nodes {
        let out_shape = node_output_shape(node, &env, &syms)?;
        for out_name in &node.outputs {
            env.insert(out_name.clone(), out_shape.clone());
            rows.push(PropagatedTensor {
                graph_id: doc.graph_id.clone(),
                tensor: out_name.clone(),
                shape: out_shape.clone(),
                node_id: node.id.clone(),
                ordinal,
            });
            ordinal += 1;
        }
    }
    Ok(rows)
}

pub fn shape_vec_to_json(shape: &ShapeVec) -> Vec<serde_json::Value> {
    shape
        .iter()
        .map(|d| match d {
            DimVal::Static(v) => serde_json::Value::from(*v),
            DimVal::Sym(s) => serde_json::Value::from(s.clone()),
        })
        .collect()
}
