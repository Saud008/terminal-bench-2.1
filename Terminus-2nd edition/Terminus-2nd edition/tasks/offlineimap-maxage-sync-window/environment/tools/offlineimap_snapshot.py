import hashlib
import json

from offlineimap_rules import filter_folders


def folder_digest(selected_names: list[str]) -> str:
    payload = json.dumps(sorted(selected_names), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_snapshot(meta: dict, rules_text: str) -> dict:
    all_names = [folder["name"] for folder in meta["folders"]]
    selected = set(filter_folders(all_names, rules_text))
    folders = []
    for folder in meta["folders"]:
        folders.append(
            {
                "name": folder["name"],
                "uidvalidity": folder["uidvalidity"],
                "selected": folder["name"] in selected,
            }
        )
    return {
        "schema": 1,
        "account": meta["account"],
        "folders": folders,
        "folder_digest": folder_digest(sorted(selected)),
    }
