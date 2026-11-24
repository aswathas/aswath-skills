"""
Extract the structured SubjectSpec from an analyst subject .ts file.

The analysis PDFs are rendered from these files, so the structured form carries
the topics, priorities, diagram specs and question banks without OCR loss.

    python extract-subject.py --ts 21cse435t.ts --out subject.json

Needs Node on PATH. The file is evaluated in a sandbox with the helpers stubbed,
so no bundler or TypeScript install is required.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PRELUDE = """
const t = (name, priority, minutes, why) => ({ name, priority, minutes, why });
const n = (name, priority, minutes, why, principles, analogy, example, diagram) =>
  ({ name, priority, minutes, why, principles, analogy, example, diagram });
const m = (id, unit, topic, question, options, correct, explanation) =>
  ({ id, unit, topic, question, options, correct, explanation, source: 'archetype' });
const q = (id, unit, marks, question, modelAnswer, keyPoints) =>
  ({ id, unit, marks, question, modelAnswer, keyPoints });
"""


def strip_ts(src: str) -> str:
    out = []
    for line in src.splitlines():
        s = line.strip()
        if s.startswith("import "):
            continue
        out.append(line)
    body = "\n".join(out)
    # export const X: SubjectSpec = {  ->  const X = {
    import re

    body = re.sub(r"export\s+const\s+(\w+)\s*:\s*SubjectSpec\s*=", r"const \1 =", body)
    m = re.search(r"const\s+(\w+)\s*=", body)
    if not m:
        raise SystemExit("could not find the subject export")
    name = m.group(1)
    return f"{PRELUDE}\n{body}\nmodule.exports = {name};\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    src = Path(a.ts).read_text(encoding="utf-8-sig")
    js = strip_ts(src)

    with tempfile.TemporaryDirectory() as d:
        mod = Path(d) / "subject.cjs"
        mod.write_text(js, encoding="utf-8")
        runner = Path(d) / "run.cjs"
        runner.write_text(
            f"const s = require({json.dumps(str(mod).replace(chr(92), '/'))});"
            f"process.stdout.write(JSON.stringify(s));",
            encoding="utf-8",
        )
        res = subprocess.run(
            ["node", str(runner)], capture_output=True, text=True, cwd=d
        )
        if res.returncode != 0:
            print(res.stderr, file=sys.stderr)
            raise SystemExit(1)
        spec = json.loads(res.stdout)

    Path(a.out).write_text(json.dumps(spec, indent=1), encoding="utf-8")
    topics = sum(len(u["topics"]) for u in spec["units"])
    print(
        f"{a.out}: {len(spec['units'])} units, {topics} topics, "
        f"{len(spec['mcqs'])} MCQs, {len(spec['partB'])} Part B, "
        f"{len(spec['partC'])} Part C"
    )


if __name__ == "__main__":
    main()
