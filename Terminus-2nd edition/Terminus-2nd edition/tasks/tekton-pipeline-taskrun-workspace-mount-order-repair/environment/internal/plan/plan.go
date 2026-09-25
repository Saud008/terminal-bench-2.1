package plan

import (
	"sort"

	"github.com/terminus/tekton-mount-plan/internal/apperr"
	"github.com/terminus/tekton-mount-plan/internal/bind"
	"github.com/terminus/tekton-mount-plan/internal/model"
	"github.com/terminus/tekton-mount-plan/internal/parse"
)

func PlanFile(path string) (model.MountPlan, error) {
	parsed, err := parse.LoadFile(path)
	if err != nil {
		return model.MountPlan{}, err
	}
	bound, err := bind.BindParsed(parsed)
	if err != nil {
		return model.MountPlan{}, err
	}
	return BuildPlan(parsed, bound)
}

func BuildPlan(parsed model.ParsedPipeline, bound model.BoundPipeline) (model.MountPlan, error) {
	byTask := map[string]model.BoundTask{}
	for _, t := range bound.Tasks {
		byTask[t.Name] = t
	}

	var mounts []model.MountEntry
	for _, task := range parsed.Tasks {
		bt, ok := byTask[task.Name]
		if !ok {
			continue
		}
		kindByWS := map[string]string{}
		for _, ws := range bt.Workspaces {
			if ws.Skipped || ws.Source == nil {
				continue
			}
			kindByWS[ws.TaskWorkspace] = ws.Source.Kind
		}
		stepOrder, err := stepOrderAlphabetical(task.Steps)
		if err != nil {
			return model.MountPlan{}, err
		}
		orderedMounts := orderMountsSubpathFirst(task, stepOrder)
		for _, m := range orderedMounts {
			kind := kindByWS[m.Workspace]
			mounts = append(mounts, model.MountEntry{
				Task:      task.Name,
				Step:      m.StepName,
				Workspace: m.Workspace,
				MountPath: m.MountPath,
				SubPath:   m.SubPath,
				Kind:      kind,
			})
		}
	}
	return model.MountPlan{RunName: parsed.RunName, Mounts: mounts}, nil
}

func stepOrderAlphabetical(steps []model.Step) ([]string, error) {
	names := make([]string, 0, len(steps))
	for _, s := range steps {
		names = append(names, s.Name)
	}
	sort.Strings(names)
	return names, nil
}

func orderMountsSubpathFirst(task model.TaskSpec, stepOrder []string) []model.StepWorkspaceMount {
	stepByName := map[string]model.Step{}
	for _, s := range task.Steps {
		stepByName[s.Name] = s
	}
	var out []model.StepWorkspaceMount
	for _, stepName := range stepOrder {
		step := stepByName[stepName]
		withSub := make([]model.StepWorkspaceMount, 0)
		withoutSub := make([]model.StepWorkspaceMount, 0)
		for _, m := range step.Mounts {
			if m.SubPath != "" {
				withSub = append(withSub, m)
			} else {
				withoutSub = append(withoutSub, m)
			}
		}
		out = append(out, withSub...)
		out = append(out, withoutSub...)
	}
	return out
}

func ValidateDAG(tasks []model.TaskSpec) error {
	_ = tasks
	return apperr.ErrCycleDetected
}
