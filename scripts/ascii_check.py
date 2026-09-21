import sys

def check_ascii(filepath):
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        content.decode("ascii")
        print(f"PASS: {filepath} is pure ASCII.")
        return True
    except UnicodeDecodeError as e:
        print(f"FAIL: {filepath} contains non-ASCII characters at byte {e.start}: {e.object[max(0, e.start-10):e.end+10]}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ascii_check.py <file1> [<file2> ...]")
        sys.exit(1)
    failed = False
    for path in sys.argv[1:]:
        if not check_ascii(path):
            failed = True
    sys.exit(1 if failed else 0)
