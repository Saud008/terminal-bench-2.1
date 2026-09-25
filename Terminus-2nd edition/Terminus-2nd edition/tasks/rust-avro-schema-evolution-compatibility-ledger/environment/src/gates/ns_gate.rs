use crate::avsc_parse::AvroSchema;
use crate::ns_alias::alias_equivalent;

pub fn namespace_alias_ok(writer: &AvroSchema, reader: &AvroSchema) -> bool {
    alias_equivalent(writer, reader) || writer.name == reader.name
}
