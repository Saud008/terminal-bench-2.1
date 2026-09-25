use broadcast_rules::rank_align_pair;
use dim_symbol::{DimVal, ShapeVec, SymbolTable};
use graph_ir::GraphNode;

pub fn node_rank_infer(
    node: &GraphNode,
    inputs: &std::collections::BTreeMap<String, ShapeVec>,
    syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    match node.op.as_str() {
        "MatMul" => infer_matmul(node, inputs, syms),
        "Add" | "Mul" => infer_broadcast(node, inputs, syms),
        "Reshape" => infer_reshape(node, inputs, syms),
        "Transpose" => infer_transpose(node, inputs),
        "Concat" => infer_concat(node, inputs, syms),
        other => Err(format!("unsupported op {other}")),
    }
}

fn infer_matmul(
    node: &GraphNode,
    inputs: &std::collections::BTreeMap<String, ShapeVec>,
    syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    let a = inputs.get(&node.inputs[0]).ok_or("missing lhs")?;
    let b = inputs.get(&node.inputs[1]).ok_or("missing rhs")?;
    if a.len() < 2 || b.len() < 2 {
        return Err("matmul rank".into());
    }
    let batch_rank = a.len().max(b.len()) - 2;
    let mut ba: ShapeVec = vec![DimVal::Static(1); batch_rank.saturating_sub(a.len() - 2)];
    ba.extend_from_slice(&a[..a.len() - 2]);
    let mut bb: ShapeVec = vec![DimVal::Static(1); batch_rank.saturating_sub(b.len() - 2)];
    bb.extend_from_slice(&b[..b.len() - 2]);
    let batch = rank_align_pair(&ba, &bb, syms).ok_or("batch broadcast")?;
    let k_lhs = &a[a.len() - 1];
    let k_rhs = &b[b.len() - 2];
    match (k_lhs, k_rhs) {
        (DimVal::Static(x), DimVal::Static(y)) if x != y => return Err("k mismatch".into()),
        (DimVal::Sym(sx), DimVal::Sym(sy)) if syms.sym_resolve(sx) != syms.sym_resolve(sy) => {
            return Err("k sym mismatch".into())
        }
        _ => {}
    }
    let mut out = batch;
    out.push(a[a.len() - 2].clone());
    out.push(b[b.len() - 1].clone());
    Ok(out)
}

fn infer_broadcast(
    node: &GraphNode,
    inputs: &std::collections::BTreeMap<String, ShapeVec>,
    syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    let a = inputs.get(&node.inputs[0]).ok_or("missing a")?;
    let b = inputs.get(&node.inputs[1]).ok_or("missing b")?;
    rank_align_pair(a, b, syms).ok_or_else(|| "broadcast fail".into())
}

fn infer_reshape(
    node: &GraphNode,
    inputs: &std::collections::BTreeMap<String, ShapeVec>,
    _syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    let in_shape = inputs.get(&node.inputs[0]).ok_or("missing in")?;
    let target = node
        .attrs
        .get("target")
        .and_then(|v| v.as_array())
        .ok_or("missing target")?;
    let mut out = Vec::new();
    let mut known = 1i64;
    let mut unknown_idx = None;
    for (i, t) in target.iter().enumerate() {
        let v = t.as_i64().ok_or("target dim")?;
        if v == -1 {
            unknown_idx = Some(i);
            out.push(DimVal::Static(-1));
        } else {
            known *= v;
            out.push(DimVal::Static(v));
        }
    }
    let total: i64 = in_shape
        .iter()
        .map(|d| match d {
            DimVal::Static(v) => *v,
            DimVal::Sym(_) => 1,
        })
        .product();
    if let Some(idx) = unknown_idx {
        out[idx] = DimVal::Static(total / known);
    }
    Ok(out)
}

fn infer_transpose(node: &GraphNode, inputs: &std::collections::BTreeMap<String, ShapeVec>) -> Result<ShapeVec, String> {
    let in_shape = inputs.get(&node.inputs[0]).ok_or("missing in")?;
    let perm = node
        .attrs
        .get("perm")
        .and_then(|v| v.as_array())
        .ok_or("perm")?;
    let mut out = vec![DimVal::Static(0); in_shape.len()];
    for (dst, p) in perm.iter().enumerate() {
        let idx = p.as_u64().ok_or("perm idx")? as usize;
        out[dst] = in_shape[idx].clone();
    }
    Ok(out)
}

fn infer_concat(
    node: &GraphNode,
    inputs: &std::collections::BTreeMap<String, ShapeVec>,
    syms: &SymbolTable,
) -> Result<ShapeVec, String> {
    let axis = node.attrs.get("axis").and_then(|v| v.as_i64()).unwrap_or(0) as usize;
    let mut shapes: Vec<&ShapeVec> = Vec::new();
    for name in &node.inputs {
        shapes.push(inputs.get(name).ok_or("missing concat input")?);
    }
    if shapes.is_empty() {
        return Err("concat empty".into());
    }
    let base = syms.materialize(shapes[0]);
    let mut out = base.clone();
    for sh in shapes.iter().skip(1) {
        let cur = syms.materialize(sh);
        if cur.len() != out.len() {
            return Err("rank mismatch".into());
        }
        for i in 0..out.len() {
            let a = out[i].clone();
            let b = cur[i].clone();
            if i == axis {
                out[i] = match (&a, &b) {
                    (DimVal::Static(x), DimVal::Static(y)) => DimVal::Static(x + y),
                    (DimVal::Sym(sx), DimVal::Sym(sy)) if sx == sy => DimVal::Sym(sx.clone()),
                    (DimVal::Sym(sx), DimVal::Sym(sy)) => {
                        if syms.sym_resolve(sx) == syms.sym_resolve(sy) {
                            DimVal::Sym(syms.sym_resolve(sx))
                        } else {
                            return Err("symbol concat mismatch".into());
                        }
                    }
                    _ => return Err("concat axis mismatch".into()),
                };
            } else if a != b {
                return Err("concat non-axis mismatch".into());
            }
        }
    }
    Ok(out)
}
