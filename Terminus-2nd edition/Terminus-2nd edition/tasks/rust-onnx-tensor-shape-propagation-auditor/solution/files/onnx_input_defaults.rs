use graph_ir::{DimSpec, TensorPort};

pub fn port_default_fill(port: &TensorPort) -> Vec<DimSpec> {
    let base = port.shape.clone();
    let Some(defaults) = &port.default_shape else {
        return base;
    };
    let mut out = Vec::with_capacity(base.len());
    for (i, cur) in base.iter().enumerate() {
        match cur {
            DimSpec::Static(-1) => {
                out.push(defaults.get(i).cloned().unwrap_or(DimSpec::Static(-1)));
            }
            other => out.push(other.clone()),
        }
    }
    while out.len() < defaults.len() {
        out.push(defaults[out.len()].clone());
    }
    out
}
