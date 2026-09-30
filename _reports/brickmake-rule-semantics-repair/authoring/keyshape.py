import re

raw = open("/mnt/c/Users/masau/stbkey.txt", "rb").read()
print("bytes:", len(raw), "BOM:", raw.startswith(b"\xef\xbb\xbf"), "lines:", raw.count(b"\n") + 1)
text = raw.decode("utf-8-sig", "replace")
shape = re.sub(r"[A-Za-z]", "a", re.sub(r"[0-9]", "9", text))
print("shape (letters->a, digits->9):", repr(shape))
