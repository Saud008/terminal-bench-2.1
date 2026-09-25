import hashlib

if __name__ == "__main__":
    print(hashlib.sha256(b"probe").hexdigest())
