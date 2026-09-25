use crate::dag::{expand_alias_chain, lookup_charset};
use crate::error::Result;
use crate::model::{
    CharsetSnapshot, CompileMeta, FontConfig, ResolveExport, SubstituteExport,
};

pub fn resolve_request(
    cfg: &FontConfig,
    charset_query: &str,
    family_query: &str,
    compile_meta: &CompileMeta,
) -> Result<ResolveExport> {
    let charset = lookup_charset(cfg, charset_query)?;
    let (alias_chain, terminal) = expand_alias_chain(cfg, &charset.alias_ref)?;
    let _terminal_entry = lookup_charset(cfg, &terminal)?;

    let encoding = charset.encoding.clone();

    let substitute = cfg
        .substitutes
        .iter()
        .find(|s| s.family == family_query)
        .map(|s| {
            let mut preferred = s.preferred.clone();
            preferred.reverse();
            SubstituteExport {
                family: s.family.clone(),
                preferred,
            }
        })
        .unwrap_or(SubstituteExport {
            family: family_query.to_string(),
            preferred: Vec::new(),
        });

    let reject_outline = cfg.reject_bitmap;
    let font_kinds_allowed = compute_font_kinds(cfg.reject_bitmap, reject_outline);

    Ok(ResolveExport {
        schema: "fc-alias-check/1".to_string(),
        charset_query: charset_query.to_string(),
        family_query: family_query.to_string(),
        charset: CharsetSnapshot {
            name: charset.name.clone(),
            short: charset.short.clone(),
            encoding: charset.encoding.clone(),
            alias_ref: charset.alias_ref.clone(),
        },
        alias_chain,
        resolved_terminal: terminal,
        encoding,
        substitute,
        reject_bitmap: cfg.reject_bitmap,
        reject_outline,
        font_kinds_allowed,
        compile_meta: compile_meta.clone(),
    })
}

fn compute_font_kinds(reject_bitmap: bool, reject_outline: bool) -> Vec<String> {
    let mut kinds = Vec::new();
    if !reject_bitmap {
        kinds.push("bitmap".to_string());
    }
    if !reject_outline {
        kinds.push("outline".to_string());
    }
    kinds
}
