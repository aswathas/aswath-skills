# The resume JSON

One file per candidate profile or per role variant. The builder
(`scripts/build_resume.py`) reads only this file; the document is generated.

```jsonc
{
  "name": "ASWATH A S",
  "headline": "Final-year B.Tech (CSE) engineer, 2027 - backend, tooling and applied-AI focus",
  "contact": ["City, Country  |  +91 ...  |  email", "linkedin  |  github  |  site"],
  "profile": "One paragraph: what the candidate ships, with numbers.",
  "education": [
    {
      "degree": "B.Tech - Computer Science & Engineering (Blockchain specialisation)",
      "school": "SRM Institute of Science and Technology, Kattankulathur",
      "when": "2023 - 2027",
      "detail": "CGPA 8.3/10 - eligible for 2027 batch roles"
    }
  ],
  "experience": [
    {
      "role": "Web3 Developer",
      "org": "SISA Infosec",
      "when": "Aug 2025 - Present",
      "points": ["Bullet written as outcome + how it was measured.", "..."]
    }
  ],
  "leadership": [
    { "role": "...", "org": "...", "when": "...", "points": ["..."] }
  ],
  "projects": [
    {
      "title": "Name - what it is",
      "right": "Stack | scale | tag",
      "points": ["...", "..."]
    }
  ],
  "skills": [
    { "label": "Languages", "text": "Python, TypeScript, ..." },
    { "label": "Backend & data", "text": "..." }
  ],
  "certifications": "One line, pipes between items.",
  "skillTags": ["Short", "tokens", "for", "search"]
}
```

## Fields that matter

| Field | Rule |
|---|---|
| `headline` | The role being applied for, plus the engineer's specialisation. It changes per variant. |
| `profile` | Numbers, not adjectives. Three lines maximum. |
| `education[].detail` | Carries the eligibility filters: batch year, CGPA. |
| `projects[].right` | The right-hand tag: stack, scale, or the competition it won. |
| `skills` | Grouped by what the JD asks for, not by a fixed taxonomy. |
| `skillTags` | Not printed. Plain keywords for search and for the site. |

## Rules

- The base profile (`~/.agents/state/resume/profile.json`) is the fallback
  profile. Variants live in `~/.agents/state/resume/variants/<slug>.json`.
- The base profile never changes because of a posting.
- Every number in a variant exists in the base profile or in a repository the
  candidate owns.
