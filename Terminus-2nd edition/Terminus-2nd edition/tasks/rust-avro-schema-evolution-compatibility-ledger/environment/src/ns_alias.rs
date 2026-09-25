use crate::avsc_parse::{full_name, AvroSchema};

pub fn resolve_type_name(writer: &AvroSchema, reader: &AvroSchema, ref_name: &str) -> bool {
    if ref_name == full_name(writer) || ref_name == full_name(reader) {
        return true;
    }
    if reader.aliases.iter().any(|a| a == ref_name) && reader.name == writer.name {
        return true;
    }
    if writer.aliases.iter().any(|a| a == ref_name) && reader.name == writer.name {
        return true;
    }
    false
}

pub fn alias_equivalent(a: &AvroSchema, b: &AvroSchema) -> bool {
    if a.name == b.name {
        return true;
    }
    let af = full_name(a);
    let bf = full_name(b);
    b.aliases.contains(&af) || a.aliases.contains(&bf)
}
