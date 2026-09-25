use crate::avsc_parse::AvroSchema;
use crate::canon_fp::parsing_fingerprint;

pub fn writer_fingerprint(schema: &AvroSchema) -> String {
    parsing_fingerprint(schema)
}

pub fn reader_fingerprint(schema: &AvroSchema) -> String {
    parsing_fingerprint(schema)
}
