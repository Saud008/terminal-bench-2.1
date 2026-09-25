"""Independent negotiation reference per /app/docs/negotiation-contract.md."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Variant:
    media_type: str
    charset: str
    language: str
    body: str


@dataclass
class Entry:
    value: str
    q: float
    pos: int


def parse_q_value(raw: str) -> tuple[str, float]:
    value = raw.strip()
    q = 1.0
    if ";" in value:
        head, tail = value.split(";", 1)
        value = head.strip()
        for part in tail.split(";"):
            part = part.strip()
            if part.lower().startswith("q="):
                try:
                    q = float(part[2:].strip())
                except ValueError:
                    pass
    return value, q


def parse_list(header: str) -> list[Entry]:
    if not header or not header.strip():
        return []
    out: list[Entry] = []
    for i, part in enumerate(header.split(",")):
        value, q = parse_q_value(part)
        if value:
            out.append(Entry(value=value, q=q, pos=i))
    return out


def media_type_match(accept_value: str, variant_type: str) -> bool:
    accept_value = accept_value.strip().lower()
    variant_type = variant_type.strip().lower()
    if accept_value == "*/*":
        return True
    if accept_value.endswith("/*"):
        prefix = accept_value[:-2]
        return variant_type.startswith(prefix + "/")
    return accept_value == variant_type


def media_type_specificity(accept_value: str) -> int:
    accept_value = accept_value.strip().lower()
    if accept_value == "*/*":
        return 0
    if accept_value.endswith("/*"):
        return 1
    return 2


def language_match(accept_lang: str, variant_lang: str) -> bool:
    accept_lang = accept_lang.strip().lower()
    variant_lang = variant_lang.strip().lower()
    if accept_lang == "*":
        return True
    if accept_lang == variant_lang:
        return True
    return variant_lang.startswith(accept_lang + "-")


def language_exactness(accept_lang: str, variant_lang: str) -> int:
    accept_lang = accept_lang.strip().lower()
    variant_lang = variant_lang.strip().lower()
    if accept_lang == variant_lang:
        return 2
    if variant_lang.startswith(accept_lang + "-"):
        return 1
    return 0


def charset_match(accept_charset: str, variant_charset: str) -> bool:
    accept_charset = accept_charset.strip().lower()
    variant_charset = variant_charset.strip().lower()
    if accept_charset == "*":
        return True
    return accept_charset == variant_charset


def prepare_headers(headers: dict[str, str]) -> dict[str, str]:
    out = dict(headers)
    if not out.get("Accept", "").strip():
        out["Accept"] = "*/*"
    if not out.get("Accept-Language", "").strip():
        out["Accept-Language"] = "*"
    return out


def negotiation_digest(
    path: str,
    resource_id: str,
    raw: dict[str, str],
    prepared: dict[str, str],
) -> str:
    import hashlib

    payload = "|".join(
        [
            path,
            resource_id,
            raw.get("Accept", ""),
            raw.get("Accept-Language", ""),
            raw.get("Accept-Charset", ""),
            prepared.get("Accept", ""),
            prepared.get("Accept-Language", ""),
            prepared.get("Accept-Charset", ""),
        ]
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def header_dict(headers: dict[str, str]) -> dict[str, str]:
    return {
        "Accept": headers.get("Accept", ""),
        "Accept-Language": headers.get("Accept-Language", ""),
        "Accept-Charset": headers.get("Accept-Charset", ""),
    }


def select_variant(variants: list[Variant], headers: dict[str, str]) -> Variant | None:
    headers = prepare_headers(headers)
    accepts = parse_list(headers.get("Accept", ""))
    if not accepts:
        accepts = [Entry(value="*/*", q=1.0, pos=0)]
    accepts = sorted(accepts, key=lambda e: (-e.q, e.pos))

    langs = parse_list(headers.get("Accept-Language", ""))
    if not langs:
        langs = [Entry(value="*", q=1.0, pos=0)]
    langs = sorted(langs, key=lambda e: (-e.q, e.pos))

    charsets = parse_list(headers.get("Accept-Charset", ""))
    charset_open = len(charsets) == 0
    if charsets:
        charsets = sorted(charsets, key=lambda e: (-e.q, e.pos))

    best: tuple[float, int, int, int, int, Variant] | None = None
    for acc in accepts:
        if acc.q <= 0:
            continue
        for lang in langs:
            if lang.q <= 0:
                continue
            charset_entries = [Entry(value="*", q=1.0, pos=0)] if charset_open else charsets
            for cs in charset_entries:
                if not charset_open and cs.q <= 0:
                    continue
                for vi, variant in enumerate(variants):
                    if not media_type_match(acc.value, variant.media_type):
                        continue
                    if not language_match(lang.value, variant.language):
                        continue
                    if not charset_open and not charset_match(cs.value, variant.charset):
                        continue
                    score = acc.q * lang.q * (cs.q if not charset_open else 1.0)
                    spec = media_type_specificity(acc.value)
                    lex = language_exactness(lang.value, variant.language)
                    key = (score, -acc.pos, spec, lex, -vi)
                    if best is None or key > (best[0], best[1], best[2], best[3], best[4]):
                        best = (score, -acc.pos, spec, lex, vi, variant)
    return best[5] if best else None


def load_variants(catalog: dict, resource_id: str) -> list[Variant]:
    raw = catalog["resources"][resource_id]["variants"]
    return [
        Variant(
            media_type=v["media_type"],
            charset=v["charset"],
            language=v["language"],
            body=v["body"],
        )
        for v in raw
    ]


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_procedural_catalog(seed: str) -> dict:
    suffix = seed.replace("-", "")[:6]
    q_a = 0.3 + (sum(seed.encode()) % 5) * 0.1
    q_b = 0.3 + (sum(seed.encode()[::-1]) % 5) * 0.1
    rid = f"proc-{suffix}"
    return {
        "resources": {
            rid: {
                "variants": [
                    {
                        "media_type": "text/plain",
                        "charset": "utf-8",
                        "language": "en",
                        "body": f"plain-{suffix}",
                    },
                    {
                        "media_type": "application/json",
                        "charset": "utf-8",
                        "language": "en",
                        "body": json.dumps({"seed": suffix, "kind": "json"}),
                    },
                ]
            }
        },
        "_accept": f"application/json;q={q_b:.1f}, text/plain;q={q_a:.1f}",
        "_resource": rid,
    }
