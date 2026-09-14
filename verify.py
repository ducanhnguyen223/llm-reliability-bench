"""Run the complete offline verification and refresh deterministic artifacts."""

import subprocess
import sys


for command in (
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
    [sys.executable, "benchmark.py"],
    [sys.executable, "replay.py"],
):
    subprocess.run(command, check=True)
