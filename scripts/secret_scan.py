import subprocess
import re
import sys

def main():
    print("=== SECRET SCAN ===")
    tracked = subprocess.check_output(["git", "ls-files"]).decode("utf-8").splitlines()
    
    # 1. Check for .env
    env_files = [f for f in tracked if ".env" in f]
    print(f"Tracked .env files: {env_files}")
    if env_files:
        print("FAIL: .env file is tracked!")
        return 1

    # 2. Check for private keys in tracked files
    explicit_key_patterns = [
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        re.compile(r"(?i)private[-_]?key\s*[:=]\s*['\"][0-9a-zA-Z]{20,}['\"]"),
        re.compile(r"(?i)mnemonic\s*[:=]\s*['\"][a-z ]{20,}['\"]"),
        re.compile(r"(?i)secret[-_]?key\s*[:=]\s*['\"][0-9a-zA-Z]{20,}['\"]"),
    ]

    violations = []
    for f in tracked:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    for pat in explicit_key_patterns:
                        if pat.search(line):
                            violations.append((f, line_no, line.strip()))
        except Exception:
            pass

    if violations:
        print("FAIL: Found potential secrets:")
        for f, ln, line in violations:
            print(f"  {f}:{ln}: {line[:80]}")
        return 1

    print("PASS: No private keys, mnemonics, or .env files found in tracked files.")

    # 3. Commit count
    commits = subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode("utf-8").strip()
    print(f"\ngit log --oneline | wc -l: {commits}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
