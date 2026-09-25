use std::collections::HashMap;

use docmodel::Document;

pub struct ServerState {
    pub docs: HashMap<String, Document>,
    pub initialized: bool,
}

impl ServerState {
    pub fn new() -> Self {
        Self {
            docs: HashMap::new(),
            initialized: false,
        }
    }
}
