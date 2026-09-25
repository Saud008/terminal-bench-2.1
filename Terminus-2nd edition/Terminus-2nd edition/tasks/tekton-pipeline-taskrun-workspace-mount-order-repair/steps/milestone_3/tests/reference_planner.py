"""Independent reference for tekton-mount-plan full pipeline."""

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
            src = {"kind": "emptyDir", "medium": as_str(ed.get("medium"))}
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
        task_spec = as_map(m.get("taskSpec"))
        steps = []
        ws_mounts = as_list(task_spec.get("workspaces"))
        for step_item in as_list(task_spec.get("steps")):
            step = as_map(step_item)
            step_name = as_str(step.get("name"))
            if not step_name:
                continue
            step_run_after = [as_str(x) for x in as_list(step.get("runAfter")) if as_str(x)]
            mounts = []
            for mount_item in ws_mounts:
                mount = as_map(mount_item)
                ws = as_str(mount.get("name"))
                mount_path = as_str(mount.get("mountPath"))
                sub_path = as_str(mount.get("subPath"))
                if ws and mount_path:
                    mounts.append(
                        {
                            "step": step_name,
                            "workspace": ws,
                            "mount_path": mount_path,
                            "sub_path": sub_path,
                        }
                    )
            steps.append({"name": step_name, "run_after": step_run_after, "mounts": mounts})
        tasks.append(
            {
                "name": name,
                "run_after": run_after,
                "workspaces": ws_refs,
                "steps": steps,
            }
        )
    return tasks


def topo_order(items: list[dict[str, Any]], name_key: str, after_key: str) -> list[str]:
    in_degree: dict[str, int] = {i[name_key]: 0 for i in items}
    children: dict[str, list[str]] = {i[name_key]: [] for i in items}
    for item in items:
        for dep in item[after_key]:
            in_degree[item[name_key]] += 1
            children.setdefault(dep, []).append(item[name_key])
    queue = [name for name, deg in in_degree.items() if deg == 0]
    order: list[str] = []
    while queue:
        cur = queue.pop(0)
        order.append(cur)
        for child in children.get(cur, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    if len(order) != len(items):
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
    order = topo_order(tasks, "name", "run_after")
    by_name = {t["name"]: t for t in tasks}
    return {
        "run_name": as_str(meta.get("name")),
        "workspace_declarations": decls,
        "pipeline_bindings": bindings,
        "tasks": [by_name[name] for name in order],
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


def reference_plan(path: Path) -> dict[str, Any]:
    parsed = reference_parse(path)
    bound = reference_bind(path)
    by_task = {t["name"]: t for t in bound["tasks"]}
    mounts: list[dict[str, Any]] = []
    for task in parsed["tasks"]:
        bt = by_task[task["name"]]
        skipped_ws = {w["task_workspace"] for w in bt["workspaces"] if w.get("skipped")}
        kind_by_ws = {
            w["task_workspace"]: w["source"]["kind"]
            for w in bt["workspaces"]
            if not w.get("skipped")
        }
        step_order = topo_order(task["steps"], "name", "run_after")
        step_by_name = {s["name"]: s for s in task["steps"]}
        for step_name in step_order:
            step = step_by_name[step_name]
            parents = [m for m in step["mounts"] if not m["sub_path"]]
            children = [m for m in step["mounts"] if m["sub_path"]]
            for mount in parents + children:
                if mount["workspace"] in skipped_ws:
                    continue
                mounts.append(
                    {
                        "task": task["name"],
                        "step": step_name,
                        "workspace": mount["workspace"],
                        "mount_path": mount["mount_path"],
                        "sub_path": mount["sub_path"],
                        "kind": kind_by_ws.get(mount["workspace"], ""),
                    }
                )
    return {"run_name": parsed["run_name"], "mounts": mounts}


def inject_step_suffix(path: Path, suffix: str, dest: Path) -> Path:
    root = load_yaml(path)
    spec = as_map(root.get("spec"))
    pipeline_spec = as_map(spec.get("pipelineSpec"))
    tasks = as_list(pipeline_spec.get("tasks"))
    for item in tasks:
        m = as_map(item)
        task_spec = as_map(m.get("taskSpec"))
        steps = as_list(task_spec.get("steps"))
        rename: dict[str, str] = {}
        for step_item in steps:
            step = as_map(step_item)
            old = as_str(step.get("name"))
            if not old:
                continue
            rename[old] = f"{old}-{suffix}"
            step["name"] = rename[old]
        for step_item in steps:
            step = as_map(step_item)
            step["runAfter"] = [rename.get(as_str(x), as_str(x)) for x in as_list(step.get("runAfter"))]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(root, sort_keys=False), encoding="utf-8")
    return dest
