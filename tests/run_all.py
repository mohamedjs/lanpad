"""Test runner executing all test suites for LANpad."""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    test_files = [
        HERE / "test_architecture.py",
        HERE / "test_protocol.py",
        HERE / "test_auth.py",
        HERE / "test_input.py",
    ]
    failed = []
    env = dict(PYTHONPATH=str(ROOT / "src"))

    for tf in test_files:
        print(f"Running {tf.name}...")
        res = subprocess.run([sys.executable, str(tf)], env=env)
        if res.returncode != 0:
            failed.append(tf.name)

    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
