use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct InterfaceInfo {
    pub id: u32,
    pub name: String,
}

pub struct InterfaceMap {
    next_id: u32,
    by_file_id: HashMap<u32, InterfaceInfo>,
    ordered: Vec<InterfaceInfo>,
}

impl InterfaceMap {
    pub fn new() -> Self {
        Self {
            next_id: 1,
            by_file_id: HashMap::new(),
            ordered: Vec::new(),
        }
    }

    pub fn register(&mut self, file_iface_id: u32, name: String) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        let info = InterfaceInfo {
            id,
            name: name.clone(),
        };
        self.by_file_id.insert(file_iface_id, info.clone());
        self.ordered.push(info);
        id
    }

    pub fn resolve(&self, raw_iface: u32) -> Option<u32> {
        self.by_file_id.get(&raw_iface).map(|i| i.id)
    }

    pub fn all(&self) -> &[InterfaceInfo] {
        &self.ordered
    }
}
