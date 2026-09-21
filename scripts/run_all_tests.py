import subprocess
import sys
import os

def run():
    print("=== 1. Checking Pure ASCII ===")
    files = [
        "contracts/full_read.py",
        "contracts/probe.py",
        "examples/consumer/consumer.py",
        "tests/fixtures/compliant.md",
        "tests/fixtures/violation_in_first_chunk.md",
        "tests/fixtures/violation_in_last_chunk.md",
    ]
    r1 = subprocess.run([sys.executable, "scripts/ascii_check.py"] + files)
    if r1.returncode != 0:
        print("ASCII check failed!")
        return 1

    print("\n=== 2. Running GenVM Linter on FullRead ===")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r2 = subprocess.run([sys.executable, "-m", "genvm_linter.cli", "check", "contracts/full_read.py"], env=env)
    if r2.returncode != 0:
        print("Linter check failed!")
        return 1

    print("\n=== 3. Running Unit Tests (Layers 1, 2, 3 & Fixtures) ===")
    r3 = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests/direct", "-p", "test_*.py"])
    if r3.returncode != 0:
        print("Unit tests failed!")
        return 1

    print("\n=== ALL PRE-DEPLOY CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(run())
