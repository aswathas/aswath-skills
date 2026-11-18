---
name: aswath-resume-tailor
description: Use when a job description, posting or role needs a tailored resume or CV, or when the user asks to tailor, rewrite, regenerate or update their resume for an internship or a full-time role.
---

## Inputs

1. **The job description.** Text pasted into the session, or a link the user
   can read. No JD means no tailoring — ask for it.
2. **The candidate profile.** A resume JSON (schema in
   `references/schema.md`). Default path:
   `~/.agents/resume/profile.json`. If it does not exist, assemble one
   from the candidate's own repositories and ask the user for the facts a
   repository cannot prove: graduation year, CGPA, contact details.
3. **The role slug.** A short name for the variant, used in the file name.

## Procedure

1. **Read the JD before the profile.** Extract what the role actually wants:
   the eligibility rules (batch year, CGPA, location), the tech stack, the
   responsibilities, and the screening stages (a coding test means DSA and a
   system or code review in the interview).
2. **Map the JD onto evidence.** One JD requirement → one bullet the candidate
   can defend in an interview. Rules in `references/jd-to-evidence.md`.
3. **Never invent.** Every number, tool, role and date comes from the profile
   JSON or a repository the user owns. If a JD keyword is missing from the
   evidence, leave it out and report it as a gap.
4. **Write the variant JSON.** Same schema as the profile, new content:
   `~/.agents/resume/variants/<role-slug>.json`. The base profile stays
   untouched — a variant is a file, not an edit.
5. **Build.**
   ```
   python scripts/build_resume.py <variant.json> <outdir> <basename>
   ```
   Writes `<basename>.docx` and `<basename>.txt`.
6. **Render the PDF.**
   ```
   soffice --headless --convert-to pdf --outdir <outdir> <basename>.docx
   ```
   LibreOffice on Windows: `"C:\Program Files\LibreOffice\program\soffice.exe"`.
7. **Verify before delivering.**
   - One page (`pypdf` page count). Two pages needs a cut, not a smaller font.
   - The extracted text carries no placeholder (`[Your City]`, `TBD`, `Lorem`).
   - Batch year, CGPA and location are present when the JD names them.
   - Every JD keyword the candidate truly has appears once, in the strongest
     place — usually a project title or the skills block.
   - The PDF text layer is readable end to end.
8. **Deliver.** Copy the `.pdf` and `.docx` to `~/Documents`, named
   `<Name>_<Company>_<Role>_Resume.pdf`, and tell the user what was dropped,
   what was reworded and what still needs a human fact.

## Commands that work

```
# build and render one variant
python scripts/build_resume.py ~/.agents/resume/variants/superdream.json \
       ~/Documents/resumes Aswath_SuperDream_SDE_Resume
soffice --headless --convert-to pdf --outdir ~/Documents/resumes \
       ~/Documents/resumes/Aswath_SuperDream_SDE_Resume.docx

# check the page count
python -c "import pypdf;print(len(pypdf.PdfReader('<pdf>').pages))"
```

## Mistakes to avoid

- **Rewriting the base profile for every posting.** Variants are files. The
  base profile is the fallback when a JD does not arrive.
- **Padding a thin project with adjectives.** "Scalable, robust, production-grade"
  on a toy project is the fastest way to lose a technical interview. Use the
  number instead: 93 tests, 8,000+ quotes, 36 exploits.
- **Keyword stuffing.** A stack that appears in five bullets but in no real
  work is a lie the interview will catch.
- **Dropping eligibility.** Batch year and CGPA are filters. If the JD names
  them, they are on the page in the education line.
- **Two pages.** An internship resume is one page. Cut projects, not type size.
- **Editing the JSON by hand in the PDF.** The JSON is the source of truth; the
  document is generated from it.

## References

- `references/schema.md` — the resume JSON: fields, meaning, required shape.
- `references/jd-to-evidence.md` — mapping a JD to bullets, honesty rules,
  ATS rules and the one-page budget.
