"""Independent reference for tekton-mount-plan parse and bind stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

APP = Path("/app")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {} if data is None else dict(data)


def as_map(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def as_str(value: Any) -> str:
    return str(value) if isinstance(value, str) else ""


def as_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def parse_workspace_decls(items: list[Any]) -> list[dict[str, Any]]:
    decls: list[dict[str, Any]] = []
    for item in items:
        m = as_map(item)
        name = as_str(m.get("name"))
        if not name:
            continue
        decls.append({"name": name, "optional": as_bool(m.get("optional"))})
    return decls


def parse_pipeline_bindings(items: list[Any]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for item in items:
        m = as_map(item)
        name = as_str(m.get("name"))
        if not name:
            continue
        src: dict[str, Any] = {}
        pvc = as_map(m.get("persistentVolumeClaim"))
        ed = as_map(m.get("emptyDir"))
        if pvc:
            src = {"kind": "persistentVolumeClaim", "claim_name": as_str(pvc.get("claimName"))}
        elif ed:
            src = {"kind": "emptyDir"}
            medium = as_str(ed.get("medium"))
            if medium:
                src["medium"] = medium
        bindings.append({"name": name, "source": src})
    return bindings


def parse_tasks(items: list[Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for item in items:
        m = as_map(item)
        name = as_str(m.get("name"))
        if not name:
            continue
        run_after = [as_str(x) for x in as_list(m.get("runAfter")) if as_str(x)]
        ws_refs = []
        for ref_item in as_list(m.get("workspaces")):
            ref = as_map(ref_item)
            ws_name = as_str(ref.get("name"))
            pipeline_ws = as_str(ref.get("workspace"))
            if ws_name and pipeline_ws:
                ws_refs.append({"name": ws_name, "workspace": pipeline_ws})
        tasks.append({"name": name, "run_after": run_after, "workspaces": ws_refs, "steps": []})
    return tasks


def task_order_topological(tasks: list[dict[str, Any]]) -> list[str]:
    in_degree: dict[str, int] = {t["name"]: 0 for t in tasks}
    children: dict[str, list[str]] = {t["name"]: [] for t in tasks}
    for task in tasks:
        for dep in task["run_after"]:
            in_degree[task["name"]] += 1
            children.setdefault(dep, []).append(task["name"])
    queue = [name for name, deg in in_degree.items() if deg == 0]
    order: list[str] = []
    while queue:
        cur = queue.pop(0)
        order.append(cur)
        for child in children.get(cur, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    if len(order) != len(tasks):
        raise ValueError("cycle detected")
    return order


def reference_parse(path: Path) -> dict[str, Any]:
    root = load_yaml(path)
    meta = as_map(root.get("metadata"))
    spec = as_map(root.get("spec"))
    pipeline_spec = as_map(spec.get("pipelineSpec"))
    decls = parse_workspace_decls(as_list(pipeline_spec.get("workspaces")))
    tasks = parse_tasks(as_list(pipeline_spec.get("tasks")))
    bindings = parse_pipeline_bindings(as_list(spec.get("workspaces")))
    order = task_order_topological(tasks)
    by_name = {t["name"]: t for t in tasks}
    ordered_tasks = [by_name[name] for name in order]
    return {
        "run_name": as_str(meta.get("name")),
        "workspace_declarations": decls,
        "pipeline_bindings": bindings,
        "tasks": ordered_tasks,
        "task_order": order,
    }


def reference_bind(path: Path) -> dict[str, Any]:
    parsed = reference_parse(path)
    binding_map = {b["name"]: b["source"] for b in parsed["pipeline_bindings"]}
    optional_names = {d["name"] for d in parsed["workspace_declarations"] if d.get("optional")}
    tasks_out: list[dict[str, Any]] = []
    for task in parsed["tasks"]:
        resolved: list[dict[str, Any]] = []
        for ref in task["workspaces"]:
            pipeline_ws = ref["workspace"]
            src = binding_map.get(pipeline_ws)
            if src is None:
                if pipeline_ws in optional_names:
                    resolved.append(
                        {
                            "task_workspace": ref["name"],
                            "pipeline_workspace": pipeline_ws,
                            "skipped": True,
                        }
                    )
                    continue
                raise ValueError(f"missing binding for {pipeline_ws}")
            resolved.append(
                {
                    "task_workspace": ref["name"],
                    "pipeline_workspace": pipeline_ws,
                    "source": src,
                    "skipped": False,
                }
            )
        tasks_out.append({"name": task["name"], "workspaces": resolved})
    return {"run_name": parsed["run_name"], "tasks": tasks_out}


def inject_workspace_claim(path: Path, claim_suffix: str, dest: Path) -> Path:
    root = load_yaml(path)
    spec = as_map(root.get("spec"))
    workspaces = as_list(spec.get("workspaces"))
    for item in workspaces:
        if not isinstance(item, dict):
            continue
        pvc = item.get("persistentVolumeClaim")
        if not isinstance(pvc, dict):
            continue
        claim = as_str(pvc.get("claimName"))
        if claim:
            pvc["claimName"] = f"{claim}-{claim_suffix}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(root, sort_keys=False), encoding="utf-8")
    return dest
