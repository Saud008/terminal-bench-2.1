use dim_symbol::{DimVal, ShapeVec, SymbolTable};

pub fn rank_align_pair(left: &ShapeVec, right: &ShapeVec, syms: &SymbolTable) -> Option<ShapeVec> {
    let la = syms.materialize(left);
    let rb = syms.materialize(right);
    let max_len = la.len().max(rb.len());
    let mut l_pad = la.clone();
    l_pad.extend(vec![DimVal::Static(1); max_len - la.len()]);
    let mut r_pad = rb.clone();
    r_pad.extend(vec![DimVal::Static(1); max_len - rb.len()]);
    let mut out = Vec::with_capacity(max_len);
    for (a, b) in l_pad.iter().zip(r_pad.iter()) {
        match (a, b) {
            (DimVal::Static(1), x) | (x, DimVal::Static(1)) => out.push(x.clone()),
            (DimVal::Static(x), DimVal::Static(y)) if x == y => out.push(DimVal::Static(*x)),
            (DimVal::Sym(sx), DimVal::Sym(sy)) if sx == sy => out.push(DimVal::Sym(sx.clone())),
            _ => return None,
        }
    }
    Some(out)
}
