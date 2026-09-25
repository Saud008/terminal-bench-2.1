package parse

import (
	"sort"

	"github.com/terminus/tekton-mount-plan/internal/apperr"
	"github.com/terminus/tekton-mount-plan/internal/model"
	"github.com/terminus/tekton-mount-plan/internal/yamlutil"
)

func LoadFile(path string) (model.ParsedPipeline, error) {
	root, err := yamlutil.ReadFile(path)
	if err != nil {
		return model.ParsedPipeline{}, apperr.ErrInvalidDocument
	}
	return ParseDocument(root)
}

func ParseDocument(root map[string]any) (model.ParsedPipeline, error) {
	kind := yamlutil.AsString(root["kind"])
	if kind != "" && kind != "PipelineRun" {
		return model.ParsedPipeline{}, apperr.ErrInvalidDocument
	}
	meta := yamlutil.AsMap(root["metadata"])
	spec := yamlutil.AsMap(root["spec"])
	if spec == nil {
		return model.ParsedPipeline{}, apperr.ErrInvalidDocument
	}
	runName := yamlutil.AsString(meta["name"])
	pipelineSpec := yamlutil.AsMap(spec["pipelineSpec"])
	if pipelineSpec == nil {
		return model.ParsedPipeline{}, apperr.ErrInvalidDocument
	}

	decls := parseWorkspaceDecls(yamlutil.AsSlice(pipelineSpec["workspaces"]))
	tasks := parseTasks(yamlutil.AsSlice(pipelineSpec["tasks"]))
	bindings := parsePipelineBindings(yamlutil.AsSlice(spec["workspaces"]))

	order, err := taskOrderAlphabetical(tasks)
	if err != nil {
		return model.ParsedPipeline{}, err
	}
	reorderTasks(&tasks, order)

	return model.ParsedPipeline{
		RunName:          runName,
		WorkspaceDecls:   decls,
		PipelineBindings: bindings,
		Tasks:            tasks,
		TaskOrder:        order,
	}, nil
}

func parseWorkspaceDecls(items []any) []model.WorkspaceDecl {
	var decls []model.WorkspaceDecl
	for _, item := range items {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		name := yamlutil.AsString(m["name"])
		if name == "" {
			continue
		}
		decls = append(decls, model.WorkspaceDecl{
			Name:     name,
			Optional: false,
		})
	}
	return decls
}

func parsePipelineBindings(items []any) []model.WorkspaceBinding {
	var bindings []model.WorkspaceBinding
	for _, item := range items {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		name := yamlutil.AsString(m["name"])
		if name == "" {
			continue
		}
		src := model.VolumeSource{}
		if pvc := yamlutil.AsMap(m["persistentVolumeClaim"]); pvc != nil {
			src.Kind = "persistentVolumeClaim"
			src.ClaimName = yamlutil.AsString(pvc["claimName"])
		} else if ed := yamlutil.AsMap(m["emptyDir"]); ed != nil {
			src.Kind = "emptyDir"
			src.Medium = yamlutil.AsString(ed["medium"])
		}
		bindings = append(bindings, model.WorkspaceBinding{Name: name, Source: src})
	}
	return bindings
}

func parseTasks(items []any) []model.TaskSpec {
	var tasks []model.TaskSpec
	for _, item := range items {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		name := yamlutil.AsString(m["name"])
		if name == "" {
			continue
		}
		runAfter := stringSlice(yamlutil.AsSlice(m["runAfter"]))
		wsRefs := parseTaskWorkspaceRefs(yamlutil.AsSlice(m["workspaces"]))
		steps := parseSteps(yamlutil.AsMap(m["taskSpec"]))
		tasks = append(tasks, model.TaskSpec{
			Name:       name,
			RunAfter:   runAfter,
			Workspaces: wsRefs,
			Steps:      steps,
		})
	}
	return tasks
}

func parseTaskWorkspaceRefs(items []any) []model.TaskWorkspaceRef {
	var refs []model.TaskWorkspaceRef
	for _, item := range items {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		name := yamlutil.AsString(m["name"])
		workspace := yamlutil.AsString(m["workspace"])
		if name == "" || workspace == "" {
			continue
		}
		refs = append(refs, model.TaskWorkspaceRef{Name: name, Workspace: workspace})
	}
	return refs
}

func parseSteps(taskSpec map[string]any) []model.Step {
	if taskSpec == nil {
		return nil
	}
	wsMounts := yamlutil.AsSlice(taskSpec["workspaces"])
	var steps []model.Step
	for _, item := range yamlutil.AsSlice(taskSpec["steps"]) {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		name := yamlutil.AsString(m["name"])
		if name == "" {
			continue
		}
		runAfter := stringSlice(yamlutil.AsSlice(m["runAfter"]))
		mounts := parseStepMounts(wsMounts, name)
		steps = append(steps, model.Step{
			Name:     name,
			RunAfter: runAfter,
			Mounts:   mounts,
		})
	}
	return steps
}

func parseStepMounts(wsItems []any, stepName string) []model.StepWorkspaceMount {
	var mounts []model.StepWorkspaceMount
	for _, item := range wsItems {
		m := yamlutil.AsMap(item)
		if m == nil {
			continue
		}
		wsName := yamlutil.AsString(m["name"])
		mountPath := yamlutil.AsString(m["mountPath"])
		subPath := yamlutil.AsString(m["subPath"])
		if wsName == "" || mountPath == "" {
			continue
		}
		mounts = append(mounts, model.StepWorkspaceMount{
			StepName:  stepName,
			Workspace: wsName,
			MountPath: mountPath,
			SubPath:   subPath,
		})
	}
	return mounts
}

func stringSlice(items []any) []string {
	var out []string
	for _, item := range items {
		s := yamlutil.AsString(item)
		if s != "" {
			out = append(out, s)
		}
	}
	return out
}

func taskOrderAlphabetical(tasks []model.TaskSpec) ([]string, error) {
	names := make([]string, 0, len(tasks))
	for _, t := range tasks {
		names = append(names, t.Name)
	}
	sort.Strings(names)
	return names, nil
}

func reorderTasks(tasks *[]model.TaskSpec, order []string) {
	byName := map[string]model.TaskSpec{}
	for _, t := range *tasks {
		byName[t.Name] = t
	}
	ordered := make([]model.TaskSpec, 0, len(order))
	for _, name := range order {
		if t, ok := byName[name]; ok {
			ordered = append(ordered, t)
		}
	}
	*tasks = ordered
}
