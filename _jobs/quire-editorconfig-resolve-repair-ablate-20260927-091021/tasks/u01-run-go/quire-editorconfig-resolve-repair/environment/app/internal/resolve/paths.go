package resolve

import "strings"

// configPaths lists the EditorConfig files that can apply to full, farthest
// first: one per directory from the root down to the file's own directory.
// The path is split on '/' as written; nothing is cleaned or resolved.
func configPaths(full, confName string) []string {
	n := strings.Count(full, "/")
	paths := make([]string, n)
	dir := full
	for i := n - 1; i >= 0; i-- {
		dir = dir[:strings.LastIndexByte(dir, '/')]
		paths[i] = dir + "/" + confName
	}
	return paths
}

// dirOf returns everything before the last '/' of path.
func dirOf(path string) string {
	return path[:strings.LastIndexByte(path, '/')]
}
