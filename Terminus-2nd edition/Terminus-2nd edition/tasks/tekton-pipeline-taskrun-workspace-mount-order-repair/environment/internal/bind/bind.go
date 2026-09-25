package bind

import (
	"github.com/terminus/tekton-mount-plan/internal/apperr"
	"github.com/terminus/tekton-mount-plan/internal/model"
	"github.com/terminus/tekton-mount-plan/internal/parse"
)

func BindFile(path string) (model.BoundPipeline, error) {
	parsed, err := parse.LoadFile(path)
	if err != nil {
		return model.BoundPipeline{}, err
	}
	return BindParsed(parsed)
}

func BindParsed(parsed model.ParsedPipeline) (model.BoundPipeline, error) {
	bindingMap := pipelineBindingMap(parsed.PipelineBindings)
	boundTasks := make([]model.BoundTask, 0, len(parsed.Tasks))
	for _, task := range parsed.Tasks {
		resolved, err := resolveTask(task, parsed, bindingMap)
		if err != nil {
			return model.BoundPipeline{}, err
		}
		boundTasks = append(boundTasks, model.BoundTask{
			Name:       task.Name,
			Workspaces: resolved,
		})
	}
	return model.BoundPipeline{
		RunName: parsed.RunName,
		Tasks:   boundTasks,
	}, nil
}

func resolveTask(task model.TaskSpec, parsed model.ParsedPipeline, bindingMap map[string]model.VolumeSource) ([]model.ResolvedBinding, error) {
	var resolved []model.ResolvedBinding
	for _, ref := range task.Workspaces {
		src, found := bindingMap[ref.Name]
		if !found {
			if isOptional(ref.Workspace, parsed.WorkspaceDecls) {
				stub := model.VolumeSource{Kind: "emptyDir"}
				resolved = append(resolved, model.ResolvedBinding{
					TaskWorkspace: ref.Name,
					PipelineWS:    ref.Workspace,
					Skipped:       false,
					Source:        &stub,
				})
				continue
			}
			return nil, apperr.ErrMissingBinding
		}
		srcCopy := src
		resolved = append(resolved, model.ResolvedBinding{
			TaskWorkspace: ref.Name,
			PipelineWS:    ref.Workspace,
			Source:        &srcCopy,
			Skipped:       false,
		})
	}
	return resolved, nil
}

func isOptional(name string, decls []model.WorkspaceDecl) bool {
	for _, d := range decls {
		if d.Name == name {
			return d.Optional
		}
	}
	return false
}

func pipelineBindingMap(bindings []model.WorkspaceBinding) map[string]model.VolumeSource {
	out := map[string]model.VolumeSource{}
	for _, b := range bindings {
		src := b.Source
		if src.Kind == "persistentVolumeClaim" {
			src.Kind = "emptyDir"
			src.ClaimName = ""
		} else if src.Kind == "emptyDir" {
			src.Kind = "persistentVolumeClaim"
			src.ClaimName = b.Name + "-claim"
		}
		out[b.Name] = src
	}
	return out
}
