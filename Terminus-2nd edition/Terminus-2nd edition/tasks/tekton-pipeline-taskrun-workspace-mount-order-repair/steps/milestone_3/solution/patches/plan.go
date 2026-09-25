package plan

import (
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
		skippedWS := map[string]bool{}
		kindByWS := map[string]string{}
		for _, ws := range bt.Workspaces {
			if ws.Skipped {
				skippedWS[ws.TaskWorkspace] = true
				continue
			}
			if ws.Source == nil {
				continue
			}
			kindByWS[ws.TaskWorkspace] = ws.Source.Kind
		}
		stepOrder, err := stepOrderTopological(task.Steps)
		if err != nil {
			return model.MountPlan{}, err
		}
		orderedMounts := orderMountsParentFirst(task, stepOrder)
		for _, m := range orderedMounts {
			if skippedWS[m.Workspace] {
				continue
			}
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

func stepOrderTopological(steps []model.Step) ([]string, error) {
	byName := map[string]model.Step{}
	inDegree := map[string]int{}
	children := map[string][]string{}
	for _, s := range steps {
		byName[s.Name] = s
		if _, ok := inDegree[s.Name]; !ok {
			inDegree[s.Name] = 0
		}
		for _, dep := range s.RunAfter {
			inDegree[s.Name]++
			children[dep] = append(children[dep], s.Name)
		}
	}
	var queue []string
	for name, deg := range inDegree {
		if deg == 0 {
			queue = append(queue, name)
		}
	}
	order := make([]string, 0, len(steps))
	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		order = append(order, cur)
		for _, child := range children[cur] {
			inDegree[child]--
			if inDegree[child] == 0 {
				queue = append(queue, child)
			}
		}
	}
	if len(order) != len(steps) {
		return nil, apperr.ErrCycleDetected
	}
	return order, nil
}

func orderMountsParentFirst(task model.TaskSpec, stepOrder []string) []model.StepWorkspaceMount {
	stepByName := map[string]model.Step{}
	for _, s := range task.Steps {
		stepByName[s.Name] = s
	}
	var out []model.StepWorkspaceMount
	for _, stepName := range stepOrder {
		step := stepByName[stepName]
		withoutSub := make([]model.StepWorkspaceMount, 0)
		withSub := make([]model.StepWorkspaceMount, 0)
		for _, m := range step.Mounts {
			if m.SubPath != "" {
				withSub = append(withSub, m)
			} else {
				withoutSub = append(withoutSub, m)
			}
		}
		out = append(out, withoutSub...)
		out = append(out, withSub...)
	}
	return out
}
