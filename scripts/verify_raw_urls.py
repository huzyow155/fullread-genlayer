import urllib.request
import hashlib
import sys

COMMIT_SHA = "1089f03d16472bf324510b52b3f73715d310ad7f"
BASE_URL = f"https://raw.githubusercontent.com/huzyow155/fullread-genlayer/{COMMIT_SHA}/tests/fixtures/"

files = [
    "compliant.md",
    "violation_in_first_chunk.md",
    "violation_in_last_chunk.md"
]

all_matched = True
for f in files:
    url = BASE_URL + f
    local_path = "tests/fixtures/" + f
    with open(local_path, "rb") as fp:
        local_bytes = fp.read()
    local_hash = hashlib.sha256(local_bytes).hexdigest()

    req = urllib.request.Request(url, headers={"User-Agent": "FullReadVerification"})
    try:
        with urllib.request.urlopen(req) as resp:
            remote_bytes = resp.read()
            remote_hash = hashlib.sha256(remote_bytes).hexdigest()
            if remote_hash == local_hash:
                print(f"PASS: {f} matches raw URL (len={len(remote_bytes)}, sha={local_hash[:16]}...)")
            else:
                print(f"FAIL: {f} hash mismatch! local={local_hash[:16]}, remote={remote_hash[:16]}")
                all_matched = False
    except Exception as e:
        print(f"ERROR: {url} -> {e}")
        all_matched = False

sys.exit(0 if all_matched else 1)
