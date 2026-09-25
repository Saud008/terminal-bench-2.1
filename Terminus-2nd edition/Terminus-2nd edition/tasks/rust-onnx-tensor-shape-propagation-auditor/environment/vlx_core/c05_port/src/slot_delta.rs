use graph_ir::{DimSpec, TensorPort};

pub fn port_default_fill(port: &TensorPort) -> Vec<DimSpec> {
    let base = port.shape.clone();
    let Some(defaults) = &port.default_shape else {
        return base;
    };
    if base.iter().any(|d| matches!(d, DimSpec::Static(-1))) {
        return base;
    }
    let mut out = Vec::with_capacity(base.len());
    for (cur, def) in base.iter().zip(defaults.iter()) {
        match cur {
            DimSpec::Static(-1) => out.push(def.clone()),
            DimSpec::Symbol(_) => out.push(cur.clone()),
            DimSpec::Static(v) => out.push(DimSpec::Static(*v)),
        }
    }
    while out.len() < defaults.len() {
        out.push(defaults[out.len()].clone());
    }
    out
}
