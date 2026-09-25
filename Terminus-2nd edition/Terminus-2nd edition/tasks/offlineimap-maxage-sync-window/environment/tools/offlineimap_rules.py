import fnmatch


def parse_rules(text: str) -> tuple[list[str], list[str]]:
    includes: list[str] = []
    excludes: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        op, pattern = line.split(None, 1)
        if op == "include":
            includes.append(pattern)
        elif op == "exclude":
            excludes.append(pattern)
    return includes, excludes


def folder_matches(name: str, includes: list[str], excludes: list[str]) -> bool:
    for pat in excludes:
        if fnmatch.fnmatchcase(name, pat):
            return False
    if not includes:
        return True
    return any(fnmatch.fnmatchcase(name, pat) for pat in includes)


def filter_folders(folder_names: list[str], rules_text: str) -> list[str]:
    includes, excludes = parse_rules(rules_text)
    return [name for name in folder_names if folder_matches(name, includes, excludes)]
