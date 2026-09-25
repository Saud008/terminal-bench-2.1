use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CharsetEntry {
    pub name: String,
    pub short: String,
    pub encoding: String,
    pub alias_ref: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SubstituteBlock {
    pub family: String,
    pub preferred: Vec<String>,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FontConfig {
    pub aliases: Vec<(String, String)>,
    pub charsets: Vec<CharsetEntry>,
    pub substitutes: Vec<SubstituteBlock>,
    pub reject_bitmap: bool,
    pub reject_outline: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompileMeta {
    pub compile_seq: u64,
    pub graph_hash: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompiledStage {
    pub schema: String,
    pub compile_meta: CompileMeta,
    pub config_path: String,
    pub inject_path: Option<String>,
    pub config: FontConfig,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResolveExport {
    pub schema: String,
    pub charset_query: String,
    pub family_query: String,
    pub charset: CharsetSnapshot,
    pub alias_chain: Vec<String>,
    pub resolved_terminal: String,
    pub encoding: String,
    pub substitute: SubstituteExport,
    pub reject_bitmap: bool,
    pub reject_outline: bool,
    pub font_kinds_allowed: Vec<String>,
    pub compile_meta: CompileMeta,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CharsetSnapshot {
    pub name: String,
    pub short: String,
    pub encoding: String,
    pub alias_ref: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SubstituteExport {
    pub family: String,
    pub preferred: Vec<String>,
}

impl FontConfig {
    pub fn merge(&mut self, other: FontConfig) {
        for (from, to) in other.aliases {
            if let Some(pos) = self.aliases.iter().position(|(f, _)| f == &from) {
                self.aliases[pos] = (from, to);
            } else {
                self.aliases.push((from, to));
            }
        }
        for cs in other.charsets {
            if let Some(pos) = self.charsets.iter().position(|c| c.name == cs.name) {
                self.charsets[pos] = cs;
            } else {
                self.charsets.push(cs);
            }
        }
        for sub in other.substitutes {
            if let Some(pos) = self.substitutes.iter().position(|s| s.family == sub.family) {
                self.substitutes[pos] = sub;
            } else {
                self.substitutes.push(sub);
            }
        }
        if other.reject_bitmap {
            self.reject_bitmap = true;
        }
        if other.reject_outline {
            self.reject_outline = true;
        }
    }
}
