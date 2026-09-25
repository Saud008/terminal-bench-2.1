package openapi

func Merge(base, ext Document) Document {
	out := Document{Paths: map[string]PathItem{}}
	for k, v := range base.Paths {
		out.Paths[k] = v
	}
	for k, v := range ext.Paths {
		out.Paths[k] = v
	}
	return out
}

func OperationFor(doc Document, method, path string) (*Operation, bool) {
	item, ok := doc.Paths[path]
	if !ok {
		return nil, false
	}
	switch method {
	case "GET":
		if item.Get == nil {
			return nil, false
		}
		return item.Get, true
	case "POST":
		if item.Post == nil {
			return nil, false
		}
		return item.Post, true
	default:
		return nil, false
	}
}
