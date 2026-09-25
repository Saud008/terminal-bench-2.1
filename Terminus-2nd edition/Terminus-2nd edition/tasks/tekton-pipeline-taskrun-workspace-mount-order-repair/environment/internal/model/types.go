package model

type WorkspaceDecl struct {
	Name     string `json:"name"`
	Optional bool   `json:"optional"`
}

type VolumeSource struct {
	Kind      string `json:"kind"`
	ClaimName string `json:"claim_name,omitempty"`
	Medium    string `json:"medium,omitempty"`
}

type WorkspaceBinding struct {
	Name   string       `json:"name"`
	Source VolumeSource `json:"source"`
}

type TaskWorkspaceRef struct {
	Name      string `json:"name"`
	Workspace string `json:"workspace"`
}

type StepWorkspaceMount struct {
	StepName  string `json:"step"`
	Workspace string `json:"workspace"`
	MountPath string `json:"mount_path"`
	SubPath   string `json:"sub_path"`
}

type TaskSpec struct {
	Name       string             `json:"name"`
	RunAfter   []string           `json:"run_after"`
	Workspaces []TaskWorkspaceRef `json:"workspaces"`
	Steps      []Step             `json:"steps"`
}

type Step struct {
	Name     string               `json:"name"`
	RunAfter []string             `json:"run_after"`
	Mounts   []StepWorkspaceMount `json:"workspace_mounts"`
}

type ParsedPipeline struct {
	RunName              string             `json:"run_name"`
	WorkspaceDecls       []WorkspaceDecl    `json:"workspace_declarations"`
	PipelineBindings     []WorkspaceBinding `json:"pipeline_bindings"`
	Tasks                []TaskSpec         `json:"tasks"`
	TaskOrder            []string           `json:"task_order"`
}

type BoundTask struct {
	Name       string             `json:"name"`
	Workspaces []ResolvedBinding  `json:"workspaces"`
}

type ResolvedBinding struct {
	TaskWorkspace string        `json:"task_workspace"`
	PipelineWS    string        `json:"pipeline_workspace"`
	Source        *VolumeSource `json:"source,omitempty"`
	Skipped       bool          `json:"skipped"`
}

type BoundPipeline struct {
	RunName string      `json:"run_name"`
	Tasks   []BoundTask `json:"tasks"`
}

type MountEntry struct {
	Task      string `json:"task"`
	Step      string `json:"step"`
	Workspace string `json:"workspace"`
	MountPath string `json:"mount_path"`
	SubPath   string `json:"sub_path"`
	Kind      string `json:"kind"`
}

type MountPlan struct {
	RunName string       `json:"run_name"`
	Mounts  []MountEntry `json:"mounts"`
}
