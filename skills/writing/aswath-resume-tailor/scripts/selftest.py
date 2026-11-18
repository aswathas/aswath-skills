"""Self-check for the resume builder.

Builds the shipped template profile and checks the output is a readable resume:
the sections are there, the bullets are there, and the text is not empty.

    python skills/writing/aswath-resume-tailor/scripts/selftest.py

Exit 0 when every case passes, 1 otherwise.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
SKILL = HERE.parent
TEMPLATE = SKILL / "assets" / "profile.template.json"
BUILDER = HERE / "build_resume.py"

SECTIONS = [
    "PROFILE",
    "EDUCATION",
    "EXPERIENCE",
    "SELECTED PROJECTS",
    "SKILLS",
    "CERTIFICATIONS & HACKATHONS",
]


def main() -> int:
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = subprocess.run(
            [sys.executable, str(BUILDER), str(TEMPLATE), str(out), "Selftest_Resume"],
            capture_output=True,
            text=True,
        )
        cases.append(("builder exits 0", result.returncode == 0, result.stderr.strip()[-200:]))
        docx = out / "Selftest_Resume.docx"
        txt = out / "Selftest_Resume.txt"
        cases.append(("docx written", docx.exists() and docx.stat().st_size > 5000, ""))
        cases.append(("txt written", txt.exists() and txt.stat().st_size > 200, ""))
        if txt.exists():
            text = txt.read_text(encoding="utf-8")
            missing = [s for s in SECTIONS if s not in text]
            cases.append(("every section present", not missing, f"missing {missing}"))
            cases.append(("bullets carry text", text.count("- ") >= 3, ""))
            cases.append(("no empty skill label", ": \n" not in text, ""))

    passed = 0
    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
        passed += 1 if ok else 0
    print(f"{passed}/{len(cases)} case(s) passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
