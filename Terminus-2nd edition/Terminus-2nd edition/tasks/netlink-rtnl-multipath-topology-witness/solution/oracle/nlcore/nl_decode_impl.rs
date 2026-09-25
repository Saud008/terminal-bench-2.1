use std::collections::BTreeMap;

use anyhow::{bail, Context, Result};

use crate::attr::*;
use crate::model::{RawHop, RawRoute};

pub fn parse_dump(data: &[u8]) -> Result<(String, Vec<RawRoute>)> {
    if data.len() < 8 || &data[0..4] != b"NLDM" {
        bail!("invalid magic");
    }
    let version = u16::from_le_bytes([data[4], data[5]]);
    if version != 1 {
        bail!("unsupported version");
    }
    let seed_len = data[6] as usize;
    let off = 7;
    if data.len() < off + seed_len + 4 {
        bail!("truncated header");
    }
    let seed = std::str::from_utf8(&data[off..off + seed_len])
        .context("seed utf8")?
        .to_string();
    let mut pos = off + seed_len;
    let count = u32::from_le_bytes(data[pos..pos + 4].try_into()?);
    pos += 4;
    let mut routes = Vec::new();
    for _ in 0..count {
        let (route, used) = parse_route(&data[pos..])?;
        pos += used;
        routes.push(route);
    }
    Ok((seed, routes))
}

fn parse_route(data: &[u8]) -> Result<(RawRoute, usize)> {
    if data.len() < 6 {
        bail!("truncated route");
    }
    let family = data[0];
    let table_id = u32::from_le_bytes(data[1..5].try_into()?);
    let dst_plen = data[5];
    let addr_len = if family == AF_INET { 4 } else { 16 };
    let mut pos = 6;
    if data.len() < pos + addr_len + 2 {
        bail!("truncated dst");
    }
    let dst = data[pos..pos + addr_len].to_vec();
    pos += addr_len;
    let attr_count = u16::from_le_bytes(data[pos..pos + 2].try_into()?);
    pos += 2;
    let mut route = RawRoute {
        family,
        table_id,
        dst,
        dst_plen,
        priority: None,
        table_attr: None,
        nh_id_hint: None,
        gateway: None,
        oif: None,
        multipath: Vec::new(),
        metrics: BTreeMap::new(),
    };
    for _ in 0..attr_count {
        if data.len() < pos + 4 {
            bail!("truncated attr header");
        }
        let atype = u16::from_le_bytes(data[pos..pos + 2].try_into()?);
        let alen = u16::from_le_bytes(data[pos + 2..pos + 4].try_into()?) as usize;
        pos += 4;
        if data.len() < pos + alen {
            bail!("truncated attr payload");
        }
        let payload = &data[pos..pos + alen];
        pos += alen;
        match atype {
            RTA_PRIORITY if alen == 4 => route.priority = Some(u32::from_le_bytes(payload.try_into()?)),
            RTA_TABLE if alen == 4 => route.table_attr = Some(u32::from_le_bytes(payload.try_into()?)),
            RTA_NH_ID if alen == 4 => route.nh_id_hint = Some(u32::from_le_bytes(payload.try_into()?)),
            RTA_OIF if alen == 4 => route.oif = Some(u32::from_le_bytes(payload.try_into()?)),
            RTA_GATEWAY => {
                let need = if family == AF_INET { 4 } else { 16 };
                if payload.len() < need {
                    bail!("gateway length");
                }
                route.gateway = Some(payload[..need].to_vec());
            }
            RTA_MULTIPATH => parse_multipath(payload, &mut route.multipath)?,
            RTA_METRICS => parse_metrics(payload, &mut route.metrics)?,
            _ => {}
        }
    }
    Ok((route, pos))
}

fn parse_multipath(payload: &[u8], out: &mut Vec<RawHop>) -> Result<()> {
    if payload.is_empty() {
        return Ok(());
    }
    let hop_count = payload[0] as usize;
    let mut pos = 1;
    for _ in 0..hop_count {
        if payload.len() < pos + 6 {
            bail!("truncated hop");
        }
        let ifindex = i32::from_le_bytes(payload[pos..pos + 4].try_into()?);
        let weight_raw = payload[pos + 4];
        let gw_family = payload[pos + 5];
        pos += 6;
        let gateway = if gw_family == 0 {
            None
        } else {
            let gw_len = if gw_family == AF_INET { 4 } else { 16 };
            if payload.len() < pos + gw_len {
                bail!("truncated gw");
            }
            let gw = payload[pos..pos + gw_len].to_vec();
            pos += gw_len;
            Some(gw)
        };
        out.push(RawHop {
            ifindex,
            weight_raw,
            gateway,
            gw_family,
        });
    }
    Ok(())
}

fn parse_metrics(payload: &[u8], out: &mut BTreeMap<String, u32>) -> Result<()> {
    if payload.is_empty() {
        return Ok(());
    }
    let count = payload[0] as usize;
    let mut pos = 1;
    for _ in 0..count {
        if payload.len() < pos + 6 {
            bail!("truncated metric");
        }
        let mtype = u16::from_le_bytes(payload[pos..pos + 2].try_into()?);
        let value = u32::from_le_bytes(payload[pos + 2..pos + 6].try_into()?);
        pos += 6;
        if let Some(name) = metric_name(mtype) {
            out.insert(name.to_string(), value);
        }
    }
    Ok(())
}
