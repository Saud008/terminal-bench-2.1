#!/usr/bin/env python3
import json
import sys

import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    data = yaml.safe_load(fh) or {}
json.dump(data, sys.stdout)
