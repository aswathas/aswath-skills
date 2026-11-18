"""Build a one-page, ATS-safe resume from a resume JSON.

The JSON is the only content source. Same schema for every role, so a tailored
variant is a new JSON, never a new builder.

  python build_resume.py <source.json> <output-dir> <basename>

Outputs in <output-dir>:
  <basename>.docx  editable
  <basename>.txt   plain-text twin (the ATS-readable copy)

PDF is a LibreOffice render of the same DOCX:
  soffice --headless --convert-to pdf --outdir <output-dir> <basename>.docx
"""

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).parent
# argv: <source.json> <output-dir> <basename>. No defaults - the caller decides the content.
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
NAME = sys.argv[3]
OUT.mkdir(parents=True, exist_ok=True)

R = json.loads(SRC.read_text(encoding="utf-8"))

INK = RGBColor(0x1A, 0x1A, 0x1A)
RULE = "9AA0A6"
ACCENT = RGBColor(0x0B, 0x35, 0x5C)
MUTED = RGBColor(0x33, 0x3A, 0x42)


def set_font(run, size, bold=False, color=INK, name="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), name)


def bottom_rule(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    borders = ppr.makeelement(qn("w:pBdr"), {})
    bottom = borders.makeelement(qn("w:bottom"), {})
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), RULE)
    borders.append(bottom)
    ppr.append(borders)


def tight(paragraph, before=0, after=0):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)


def patch_bullet_font(doc):
    """The stock List Bullet style draws its bullet from SymbolMT, which lands in
    the PDF as a private-use codepoint some ATS parsers drop. Point the level at
    Calibri's real bullet so the extracted text layer keeps it."""
    numbering = doc.part.numbering_part.element
    num_id = doc.styles["List Bullet"].element.find(
        ".//" + qn("w:numPr") + "/" + qn("w:numId")
    ).get(qn("w:val"))
    abstract_id = None
    for num in numbering.findall(qn("w:num")):
        if num.get(qn("w:numId")) == num_id:
            abstract_id = num.find(qn("w:abstractNumId")).get(qn("w:val"))
    for abstract in numbering.findall(qn("w:abstractNum")):
        if abstract.get(qn("w:abstractNumId")) != abstract_id:
            continue
        for lvl in abstract.findall(qn("w:lvl")):
            if lvl.get(qn("w:ilvl")) != "0":
                continue
            lvl.find(qn("w:lvlText")).set(qn("w:val"), "•")
            rpr = lvl.find(qn("w:rPr"))
            if rpr is None:
                rpr = lvl.makeelement(qn("w:rPr"), {})
                lvl.append(rpr)
            fonts = rpr.find(qn("w:rFonts"))
            if fonts is None:
                fonts = rpr.makeelement(qn("w:rFonts"), {})
                rpr.append(fonts)
            for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:sym"):
                fonts.set(qn(attr), "Calibri")


def heading(doc, text):
    h = doc.add_paragraph()
    tight(h, before=6, after=2)
    set_font(h.add_run(text), 10, bold=True, color=ACCENT)
    bottom_rule(h)


def entry(doc, title, right, bullets, sub=None):
    p = doc.add_paragraph()
    tight(p, before=2.5, after=0.5)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(18.3), WD_TAB_ALIGNMENT.RIGHT)
    set_font(p.add_run(title), 9.4, bold=True)
    set_font(p.add_run("\t" + right), 9.0, color=MUTED)
    if sub:
        sp = doc.add_paragraph()
        tight(sp, after=1.2)
        sp.paragraph_format.left_indent = Cm(0.42)
        set_font(sp.add_run(sub), 9.2)
    for b in bullets:
        bp = doc.add_paragraph(style="List Bullet")
        tight(bp, after=1.2)
        bp.paragraph_format.left_indent = Cm(0.42)
        bp.paragraph_format.first_line_indent = Cm(-0.42)
        set_font(bp.add_run(b), 9.2)


def build():
    doc = Document()
    patch_bullet_font(doc)

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.1)
    section.bottom_margin = Cm(1.0)
    section.left_margin = Cm(1.35)
    section.right_margin = Cm(1.35)
    section.header_distance = Cm(0.6)
    section.footer_distance = Cm(0.6)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0

    p = doc.add_paragraph()
    tight(p)
    set_font(p.add_run(R["name"]), 16.5, bold=True)

    p = doc.add_paragraph()
    tight(p, before=1, after=2)
    set_font(p.add_run(R["headline"]), 9.5, bold=True, color=MUTED)

    for i, line in enumerate(R["contact"]):
        p = doc.add_paragraph()
        tight(p, after=0 if i < len(R["contact"]) - 1 else 3)
        set_font(p.add_run(line), 8.8, color=MUTED)
    bottom_rule(doc.paragraphs[-1])

    heading(doc, "PROFILE")
    p = doc.add_paragraph()
    tight(p, after=1.5)
    set_font(p.add_run(R["profile"]), 9.3)

    heading(doc, "EDUCATION")
    for e in R["education"]:
        entry(doc, e["degree"], e["when"], [], sub=f"{e['school']} - {e['detail']}.")

    heading(doc, "EXPERIENCE")
    for e in R["experience"]:
        entry(doc, f"{e['role']} - {e['org']}", e["when"], e["points"])

    heading(doc, "LEADERSHIP")
    for e in R["leadership"]:
        entry(doc, f"{e['role']} - {e['org']}", e["when"], e["points"])

    heading(doc, "SELECTED PROJECTS")
    for p_ in R["projects"]:
        entry(doc, p_["title"], p_["right"], p_["points"])

    heading(doc, "SKILLS")
    for s in R["skills"]:
        p = doc.add_paragraph()
        tight(p, after=1.5)
        set_font(p.add_run(f"{s['label']}: "), 9.3, bold=True)
        set_font(p.add_run(s["text"]), 9.3)

    heading(doc, "CERTIFICATIONS & HACKATHONS")
    p = doc.add_paragraph()
    tight(p, after=1.5)
    set_font(p.add_run(R["certifications"]), 9.3)

    doc.save(str(OUT / f"{NAME}.docx"))

    lines = [R["name"], R["headline"], ""] + R["contact"] + [""]
    lines += ["PROFILE", R["profile"], ""]
    lines += ["EDUCATION"]
    for e in R["education"]:
        lines += [f"{e['degree']} | {e['when']}", f"- {e['school']} - {e['detail']}."]
    lines += [""]
    for label, key in (("EXPERIENCE", "experience"), ("LEADERSHIP", "leadership")):
        lines += [label]
        for e in R[key]:
            lines += [f"{e['role']} - {e['org']} | {e['when']}"]
            lines += [f"- {b}" for b in e["points"]]
        lines += [""]
    lines += ["SELECTED PROJECTS"]
    for p_ in R["projects"]:
        lines += [f"{p_['title']} | {p_['right']}"]
        lines += [f"- {b}" for b in p_["points"]]
    lines += [""]
    lines += ["SKILLS"]
    lines += [f"{s['label']}: {s['text']}" for s in R["skills"]]
    lines += ["", "CERTIFICATIONS & HACKATHONS", R["certifications"], ""]
    (OUT / f"{NAME}.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    build()
