import re

h = re.compile(rb"(?<![A-Za-z0-9_.-])/home/(?!agent\b|app\b|user\b|ubuntu\b|runner\b|node\b)[A-Za-z0-9_.-]+")
for s in [b"/tmp/t3/home/git", b" /home/masau/x", b'"/home/masau', b"HOME=/home/bob", b"/home/agent/x", b"/tmp/gleaner-case/user"]:
    print(s, bool(h.search(s)))
