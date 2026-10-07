"""Build the zip that gets uploaded to Colab.

Ships the code, the benchmark, the generated answers and both caches, so the
Colab run starts from exactly the state the laptop run ended in:

* ``outputs/answers.json``  - the answers under evaluation, generated once.
  Without this, Colab would generate new answers and nothing would be
  comparable.
* ``cache/``                - every LLM call, keyed by hash(model + prompt +
  parameters). Calls whose model is unchanged replay for free; calls with a new
  model miss and run, which is exactly what we want to measure.
* ``data/evidence/``        - cached Wikipedia pages, so retrieval is shared
  between runs and Colab's datacenter IP hits the rate limiter less.

    python colab/make_bundle.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "colab" / "verifact_lite_bundle.zip"

# (path relative to repo root, required)
INCLUDE_DIRS = [
    ("src", True),
    ("experiments", True),
    ("tests", True),
    ("colab", True),
    ("data", True),       # challenge set, reference facts and the evidence cache
    ("cache", False),     # LLM call cache; large-ish but worth shipping
]
INCLUDE_FILES = [
    ("config.yaml", True),
    ("requirements.txt", True),
    ("README.md", False),
    ("demo.py", False),
    ("outputs/answers.json", True),
    ("outputs/summary.json", False),      # laptop results, for side-by-side
    ("outputs/comparison.csv", False),
]
SKIP_PARTS = {"__pycache__", ".pytest_cache", "node_modules", "render", ".git"}


def wanted(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    if path.resolve() == OUT.resolve():
        return False  # the bundle lives in colab/, which is itself bundled
    return path.suffix not in {".pyc", ".pptx", ".zip"}


def main() -> None:
    if OUT.exists():
        OUT.unlink()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for rel, required in INCLUDE_DIRS:
            base = ROOT / rel
            if not base.exists():
                if required:
                    missing.append(rel)
                continue
            for path in base.rglob("*"):
                if path.is_file() and wanted(path):
                    zf.write(path, path.relative_to(ROOT).as_posix())
                    count += 1
        for rel, required in INCLUDE_FILES:
            path = ROOT / rel
            if not path.exists():
                if required:
                    missing.append(rel)
                continue
            zf.write(path, path.relative_to(ROOT).as_posix())
            count += 1

    if missing:
        print("ERROR: required paths are missing: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(1)

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"wrote {OUT}")
    print(f"  {count} files, {size_mb:.1f} MB")
    print("\nUpload this file in the Colab notebook's 'Upload the bundle' cell.")


if __name__ == "__main__":
    main()
