use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DimVal {
    Static(i64),
    Sym(String),
}

pub type ShapeVec = Vec<DimVal>;

#[derive(Debug, Clone, Default)]
pub struct SymbolTable {
    parent: HashMap<String, String>,
}

impl SymbolTable {
    pub fn new() -> Self {
        Self { parent: HashMap::new() }
    }

    pub fn sym_link(&mut self, left: &str, right: &str) {
        let rl = self.sym_resolve(left);
        let rr = self.sym_resolve(right);
        if rl != rr {
            self.parent.insert(rr, rl);
        }
    }

    pub fn sym_resolve(&self, sym: &str) -> String {
        let mut cur = sym.to_string();
        while let Some(next) = self.parent.get(&cur) {
            if next == &cur {
                break;
            }
            cur = next.clone();
        }
        cur
    }

    pub fn merge_dim_specs(&self, a: &ShapeVec, b: &ShapeVec) -> Option<ShapeVec> {
        if a.len() != b.len() {
            return None;
        }
        let mut out = Vec::with_capacity(a.len());
        for (da, db) in a.iter().zip(b.iter()) {
            match (da, db) {
                (DimVal::Static(x), DimVal::Static(y)) if x == y => out.push(DimVal::Static(*x)),
                (DimVal::Static(x), DimVal::Static(_)) => return None,
                (DimVal::Static(v), DimVal::Sym(s)) | (DimVal::Sym(s), DimVal::Static(v)) => {
                    out.push(DimVal::Static(*v));
                    let _ = self.sym_resolve(s);
                }
                (DimVal::Sym(sa), DimVal::Sym(sb)) => {
                    let ra = self.sym_resolve(sa);
                    let rb = self.sym_resolve(sb);
                    if ra == rb {
                        out.push(DimVal::Sym(ra));
                    } else {
                        return None;
                    }
                }
            }
        }
        Some(out)
    }

    pub fn materialize(&self, shape: &ShapeVec) -> ShapeVec {
        shape
            .iter()
            .map(|d| match d {
                DimVal::Static(v) => DimVal::Static(*v),
                DimVal::Sym(s) => DimVal::Sym(self.sym_resolve(s)),
            })
            .collect()
    }
}

pub fn parse_dim_specs(specs: &[graph_ir::DimSpec]) -> ShapeVec {
    specs
        .iter()
        .map(|d| match d {
            graph_ir::DimSpec::Static(v) => DimVal::Static(*v),
            graph_ir::DimSpec::Symbol(s) => DimVal::Sym(s.clone()),
        })
        .collect()
}
