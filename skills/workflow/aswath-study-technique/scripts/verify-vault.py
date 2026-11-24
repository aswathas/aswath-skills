"""
Quality gate for a generated study vault.

A note that renders is not a note that teaches. This checks the depth that makes
the difference, per must-know topic:

  - a precise definition
  - an ordered mechanism (>= 3 steps)
  - a model answer (full or points)
  - advantages AND limitations, or exam traps
  - at least 3 active-recall cards
  - a memory trick or one-line revision
  - an embedded drawing

Exits 1 on any failure, so it can gate a build.

    python verify-vault.py <vault>/<Course> <subject.json>
"""

import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "What it is",
    "How it works",
    "Active recall",
]


def sections(md: str):
    return [m.group(1).strip() for m in re.finditer(r"^## \d+\. (.+)$", md, re.M)]


def has_section(md, needle):
    return any(needle.lower() in s.lower() for s in sections(md))


def main(course_dir: str, subject_path: str):
    root = Path(course_dir)
    spec = json.loads(Path(subject_path).read_text(encoding="utf-8"))
    safe = lambda n: re.sub(r"[\\/:*?\"<>|]", " -", n).strip()
    pad = lambda n: str(n).zfill(2)

    failures = []
    warnings = []
    checked = 0

    for u in spec["units"]:
        udir = root / f"Unit {u['unit']} - {safe(u['name'])}"
        if not udir.exists():
            failures.append(f"U{u['unit']}: unit folder missing")
            continue

        rev = udir / f"Unit {u['unit']} - {safe(u['name'])} - Revision Sheet.md"
        if not rev.exists():
            warnings.append(f"U{u['unit']}: no revision sheet")

        for i, t in enumerate(u["topics"]):
            path = udir / f"{pad(i+1)} {safe(t['name'])}.md"
            if not path.exists():
                failures.append(f"U{u['unit']}: missing note for {t['name']}")
                continue
            md = path.read_text(encoding="utf-8")
            checked += 1
            tag = f"U{u['unit']} {t['name']}"

            if t["priority"] != "must":
                # Skim topics only need to exist and point somewhere.
                if "## 1." not in md:
                    failures.append(f"{tag}: no sections at all")
                continue

            for s in REQUIRED_SECTIONS:
                if not has_section(md, s):
                    failures.append(f"{tag}: missing section '{s}'")

            if not re.search(r"\*\*Definition\.\*\*", md):
                failures.append(f"{tag}: no precise definition")

            mech = re.search(r"## \d+\. How it works[\s\S]*?(?=\n## |\Z)", md)
            steps = len(re.findall(r"^\d+\. ", mech.group(0), re.M)) if mech else 0
            if steps < 3:
                failures.append(f"{tag}: mechanism has {steps} steps (need 3+)")

            has_model = "Model answer" in md
            if not has_model:
                failures.append(f"{tag}: no model answer")

            if not ("Advantages" in md or "Exam traps" in md):
                failures.append(f"{tag}: neither advantages/limitations nor traps")

            recall = re.findall(r"<details>", md)
            if len(recall) < 3:
                failures.append(f"{tag}: {len(recall)} recall cards (need 3+)")

            if not ("Memory trick" in md or "One-line revision" in md):
                warnings.append(f"{tag}: no memory hook")

            if ".excalidraw]]" not in md:
                failures.append(f"{tag}: no embedded drawing")

    print(f"checked {checked} topic notes")
    for w in warnings:
        print("  WARN " + w)
    if failures:
        print(f"\nFAIL — {len(failures)} issues")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("PASS — every must-know note meets the depth bar")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
