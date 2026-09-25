use avsc_json::{full_name, AvroSchema};

pub fn resolve_type_name(writer: &AvroSchema, reader: &AvroSchema, ref_name: &str) -> bool {
    let writer_full = full_name(writer);
    let reader_full = full_name(reader);
    if ref_name == writer_full || ref_name == reader_full {
        return true;
    }
    if writer.aliases.iter().any(|a| a == ref_name) {
        return reader_full.ends_with(&writer.name);
    }
    if reader.aliases.iter().any(|a| a == ref_name) {
        return writer_full.ends_with(&reader.name);
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
