use graph_ir::TensorPort;

pub fn port_dim_specs(port: &TensorPort) -> Vec<graph_ir::DimSpec> {
    input_defaults::port_default_fill(port)
}
