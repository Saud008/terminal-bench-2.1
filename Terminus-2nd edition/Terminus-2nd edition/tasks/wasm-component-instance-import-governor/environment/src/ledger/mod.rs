use std::fs;
use std::io::{Read, Write};
use std::path::Path;

use crate::types::{ImportAliasLedger, LedgerComponent, ParsedComponent};
use crate::{LEDGER_MAGIC, DEFAULT_LEDGER_PATH};

pub fn bump_ingest_seq(path: &str) -> u32 {
    if let Ok(ledger) = load_ledger(path) {
        ledger.ingest_seq + 1
    } else {
        1
    }
}

pub fn save_ledger(path: &str, ledger: &ImportAliasLedger) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let mut buf = Vec::new();
    write_ledger(&mut buf, ledger)?;
    fs::write(path, buf).map_err(|e| e.to_string())
}

pub fn load_ledger(path: &str) -> Result<ImportAliasLedger, String> {
    let raw = fs::read(path).map_err(|e| e.to_string())?;
    let mut cursor = std::io::Cursor::new(raw);
    read_ledger(&mut cursor)
}

pub fn from_parsed(seq: u32, parsed: Vec<ParsedComponent>) -> ImportAliasLedger {
    ImportAliasLedger {
        ingest_seq: seq,
        components: parsed
            .into_iter()
            .map(|p| LedgerComponent {
                filename: p.filename,
                raw: p.raw,
                imports: p.imports,
                aliases: p.aliases,
                export_section_len: p.export_section_len,
                exports: p.exports,
                reexports: p.reexports,
            })
            .collect(),
    }
}

fn write_ledger<W: Write>(w: &mut W, ledger: &ImportAliasLedger) -> Result<(), String> {
    w.write_all(LEDGER_MAGIC).map_err(|e| e.to_string())?;
    w.write_all(&ledger.ingest_seq.to_le_bytes())
        .map_err(|e| e.to_string())?;
    let count = ledger.components.len() as u16;
    w.write_all(&count.to_le_bytes()).map_err(|e| e.to_string())?;
    for comp in &ledger.components {
        write_component(w, comp)?;
    }
    Ok(())
}

fn write_component<W: Write>(w: &mut W, comp: &LedgerComponent) -> Result<(), String> {
    let name = comp.filename.as_bytes();
    if name.len() > 255 {
        return Err("filename too long".into());
    }
    w.write_all(&[name.len() as u8]).map_err(|e| e.to_string())?;
    w.write_all(name).map_err(|e| e.to_string())?;
    w.write_all(&(comp.raw.len() as u32).to_le_bytes())
        .map_err(|e| e.to_string())?;
    w.write_all(&comp.raw).map_err(|e| e.to_string())?;
    w.write_all(&(comp.imports.len() as u16).to_le_bytes())
        .map_err(|e| e.to_string())?;
    for imp in &comp.imports {
        write_import(w, imp)?;
    }
    w.write_all(&(comp.aliases.len() as u16).to_le_bytes())
        .map_err(|e| e.to_string())?;
    for alias in &comp.aliases {
        w.write_all(&alias.local.to_le_bytes())
            .map_err(|e| e.to_string())?;
        w.write_all(&alias.module_type.to_le_bytes())
            .map_err(|e| e.to_string())?;
    }
    w.write_all(&comp.export_section_len.to_le_bytes())
        .map_err(|e| e.to_string())?;
    w.write_all(&(comp.exports.len() as u16).to_le_bytes())
        .map_err(|e| e.to_string())?;
    for exp in &comp.exports {
        w.write_all(&[exp.kind]).map_err(|e| e.to_string())?;
        let nb = exp.name.as_bytes();
        w.write_all(&[nb.len() as u8]).map_err(|e| e.to_string())?;
        w.write_all(nb).map_err(|e| e.to_string())?;
        let inst = exp.instance_target.unwrap_or(0xffff);
        w.write_all(&inst.to_le_bytes()).map_err(|e| e.to_string())?;
    }
    w.write_all(&(comp.reexports.len() as u16).to_le_bytes())
        .map_err(|e| e.to_string())?;
    for edge in &comp.reexports {
        let ob = edge.outer.as_bytes();
        w.write_all(&[ob.len() as u8]).map_err(|e| e.to_string())?;
        w.write_all(ob).map_err(|e| e.to_string())?;
        w.write_all(&edge.via_instance.to_le_bytes())
            .map_err(|e| e.to_string())?;
        let ib = edge.inner.as_bytes();
        w.write_all(&[ib.len() as u8]).map_err(|e| e.to_string())?;
        w.write_all(ib).map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn write_import<W: Write>(w: &mut W, imp: &crate::types::ImportRow) -> Result<(), String> {
    let mb = imp.module.as_bytes();
    let nb = imp.name.as_bytes();
    w.write_all(&[mb.len() as u8]).map_err(|e| e.to_string())?;
    w.write_all(mb).map_err(|e| e.to_string())?;
    w.write_all(&[nb.len() as u8]).map_err(|e| e.to_string())?;
    w.write_all(nb).map_err(|e| e.to_string())?;
    w.write_all(&imp.type_local.to_le_bytes())
        .map_err(|e| e.to_string())?;
    Ok(())
}

fn read_ledger<R: Read>(r: &mut R) -> Result<ImportAliasLedger, String> {
    let mut magic = [0u8; 4];
    r.read_exact(&mut magic).map_err(|e| e.to_string())?;
    if &magic != LEDGER_MAGIC {
        return Err("bad ledger magic".into());
    }
    let mut seq_b = [0u8; 4];
    r.read_exact(&mut seq_b).map_err(|e| e.to_string())?;
    let ingest_seq = u32::from_le_bytes(seq_b);
    let mut count_b = [0u8; 2];
    r.read_exact(&mut count_b).map_err(|e| e.to_string())?;
    let count = u16::from_le_bytes(count_b) as usize;
    let mut components = Vec::with_capacity(count);
    for _ in 0..count {
        components.push(read_component(r)?);
    }
    Ok(ImportAliasLedger {
        ingest_seq,
        components,
    })
}

fn read_component<R: Read>(r: &mut R) -> Result<LedgerComponent, String> {
    let mut nlen = [0u8; 1];
    r.read_exact(&mut nlen).map_err(|e| e.to_string())?;
    let mut name = vec![0u8; nlen[0] as usize];
    r.read_exact(&mut name).map_err(|e| e.to_string())?;
    let filename = String::from_utf8(name).map_err(|e| e.to_string())?;
    let mut raw_len_b = [0u8; 4];
    r.read_exact(&mut raw_len_b).map_err(|e| e.to_string())?;
    let raw_len = u32::from_le_bytes(raw_len_b) as usize;
    let mut raw = vec![0u8; raw_len];
    r.read_exact(&mut raw).map_err(|e| e.to_string())?;
    let mut imp_count_b = [0u8; 2];
    r.read_exact(&mut imp_count_b).map_err(|e| e.to_string())?;
    let imp_count = u16::from_le_bytes(imp_count_b) as usize;
    let mut imports = Vec::with_capacity(imp_count);
    for _ in 0..imp_count {
        imports.push(read_import_row(r)?);
    }
    let mut alias_count_b = [0u8; 2];
    r.read_exact(&mut alias_count_b).map_err(|e| e.to_string())?;
    let alias_count = u16::from_le_bytes(alias_count_b) as usize;
    let mut aliases = Vec::with_capacity(alias_count);
    for _ in 0..alias_count {
        let mut lb = [0u8; 2];
        r.read_exact(&mut lb).map_err(|e| e.to_string())?;
        let local = u16::from_le_bytes(lb);
        r.read_exact(&mut lb).map_err(|e| e.to_string())?;
        let module_type = u16::from_le_bytes(lb);
        aliases.push(crate::types::TypeAlias { local, module_type });
    }
    let mut esl = [0u8; 4];
    r.read_exact(&mut esl).map_err(|e| e.to_string())?;
    let export_section_len = u32::from_le_bytes(esl);
    let mut exp_count_b = [0u8; 2];
    r.read_exact(&mut exp_count_b).map_err(|e| e.to_string())?;
    let exp_count = u16::from_le_bytes(exp_count_b) as usize;
    let mut exports = Vec::with_capacity(exp_count);
    for _ in 0..exp_count {
        let mut kind = [0u8; 1];
        r.read_exact(&mut kind).map_err(|e| e.to_string())?;
        let mut nl = [0u8; 1];
        r.read_exact(&mut nl).map_err(|e| e.to_string())?;
        let mut nb = vec![0u8; nl[0] as usize];
        r.read_exact(&mut nb).map_err(|e| e.to_string())?;
        let name = String::from_utf8(nb).map_err(|e| e.to_string())?;
        let mut ib = [0u8; 2];
        r.read_exact(&mut ib).map_err(|e| e.to_string())?;
        let inst_raw = u16::from_le_bytes(ib);
        let instance_target = if inst_raw == 0xffff {
            None
        } else {
            Some(inst_raw)
        };
        exports.push(crate::types::WireExport {
            kind: kind[0],
            name,
            instance_target,
        });
    }
    let mut re_count_b = [0u8; 2];
    r.read_exact(&mut re_count_b).map_err(|e| e.to_string())?;
    let re_count = u16::from_le_bytes(re_count_b) as usize;
    let mut reexports = Vec::with_capacity(re_count);
    for _ in 0..re_count {
        let mut ol = [0u8; 1];
        r.read_exact(&mut ol).map_err(|e| e.to_string())?;
        let mut ob = vec![0u8; ol[0] as usize];
        r.read_exact(&mut ob).map_err(|e| e.to_string())?;
        let outer = String::from_utf8(ob).map_err(|e| e.to_string())?;
        let mut vb = [0u8; 2];
        r.read_exact(&mut vb).map_err(|e| e.to_string())?;
        let via_instance = u16::from_le_bytes(vb);
        let mut il = [0u8; 1];
        r.read_exact(&mut il).map_err(|e| e.to_string())?;
        let mut ib = vec![0u8; il[0] as usize];
        r.read_exact(&mut ib).map_err(|e| e.to_string())?;
        let inner = String::from_utf8(ib).map_err(|e| e.to_string())?;
        reexports.push(crate::types::ReexportEdge {
            outer,
            via_instance,
            inner,
        });
    }
    Ok(LedgerComponent {
        filename,
        raw,
        imports,
        aliases,
        export_section_len,
        exports,
        reexports,
    })
}

fn read_import_row<R: Read>(r: &mut R) -> Result<crate::types::ImportRow, String> {
    let mut ml = [0u8; 1];
    r.read_exact(&mut ml).map_err(|e| e.to_string())?;
    let mut mb = vec![0u8; ml[0] as usize];
    r.read_exact(&mut mb).map_err(|e| e.to_string())?;
    let module = String::from_utf8(mb).map_err(|e| e.to_string())?;
    let mut nl = [0u8; 1];
    r.read_exact(&mut nl).map_err(|e| e.to_string())?;
    let mut nb = vec![0u8; nl[0] as usize];
    r.read_exact(&mut nb).map_err(|e| e.to_string())?;
    let name = String::from_utf8(nb).map_err(|e| e.to_string())?;
    let mut tb = [0u8; 2];
    r.read_exact(&mut tb).map_err(|e| e.to_string())?;
    let type_local = u16::from_le_bytes(tb);
    Ok(crate::types::ImportRow {
        module,
        name,
        type_local,
    })
}

pub fn default_ledger_path() -> &'static str {
    DEFAULT_LEDGER_PATH
}
