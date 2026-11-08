"""Run the midterm pipeline end to end (no API key needed).

Steps:
  1. validate the saved LLM extractions against the JSON schema
  2. build ground-truth graphs from the two apps' deployment configs
  3. score extraction (precision / recall / F1)
  4. build graphs, stats, failure-impact labels, composite heuristic,
     soft-dependency check, figures
  5. rebuild the name-blind document and score the saved blind runs
     (repeat runs and name-blind runs in extracted_blind/)
  6. run the automated test suite

To re-run the LLM extraction itself first:  python src/extractor.py
"""
import random
import subprocess
import sys

import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

steps = [
    [sys.executable, "src/extractor.py", "--validate-only"],
    [sys.executable, "src/ground_truth.py", "--repo-ob", "../microservices-demo",
     "--repo-otel", "../opentelemetry-demo"],
    [sys.executable, "src/evaluate_extraction.py"],
    [sys.executable, "src/build_graph.py"],
    [sys.executable, "src/anonymize.py"],
    [sys.executable, "src/blind_runs.py"],
    [sys.executable, "-m", "pytest", "-q", "tests"],
]
for cmd in steps:
    print("\n$", " ".join(cmd[1:]))
    subprocess.run(cmd, check=True)
print("\nDone. Outputs in results/ and figures/.")
