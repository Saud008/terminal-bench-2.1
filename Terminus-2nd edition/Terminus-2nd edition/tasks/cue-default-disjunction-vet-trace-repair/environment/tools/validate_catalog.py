"""Catalog manifest validation utilities."""

def workspace_names(catalog: dict) -> list[str]:
    return [row["name"] for row in catalog.get("workspaces", [])]
