# JD to evidence

## The mapping

Read the JD top to bottom and pull four lists.

| From the JD | What it does to the resume |
|---|---|
| Eligibility (batch year, CGPA, location, gender, work authorisation) | Goes in the education line or the contact line. These are filters, not decoration. |
| Named stack (Python, FastAPI, React, Docker, ...) | Goes in the skills block, and in the project that really uses it. |
| Responsibilities ("build APIs", "own a service", "fix bugs") | The verbs pick which project goes on top. |
| Screening stages (coding test, technical interview, HR) | Decides the emphasis. A test means DSA and a real codebase. An interview means depth in one project. |

Then, for each named requirement, find one piece of evidence:

```
JD requirement  ->  evidence  ->  one bullet  ->  where it sits
```

A requirement with no evidence is a gap to report, not a bullet to invent.

## Writing the bullet

A bullet is: **what you built or did** + **how it was measured**.

- "Shipped 53 tools over live NSE/BSE data - quotes for 8,000+ stocks,
  indicators, screeners, backtests - so decisions run on real data instead of a
  paywalled terminal."
- "Cut reporting context from 32,450 to 142 tokens and latency from 4.8s to
  1.1s, measured across 60 vehicles x 3 delivery modes."

Not: "Built a robust market data solution using Python and APIs."

Adjectives are the last thing to add and usually never needed. A number is
worth ten adjectives.

## Honesty rules

1. Every claim is traceable to the profile JSON or to a repository the
   candidate owns.
2. A tool that appears only in a wishlist does not appear on the resume.
3. "Built", "shipped", "led" and "authored" mean what they say. If the work was
   a team effort, name the role: "built the backend while two others built
   the UI".
4. Never fabricate an employer, a date, a CGPA, a batch year or a number.
5. A gap in the evidence is stated to the user, in the delivery message. The
   resume is the honest document; the gap list is the honest report.

## ATS rules

- Single column. No tables, no text boxes, no headers in the page header.
- Section headings in caps: PROFILE, EDUCATION, EXPERIENCE, LEADERSHIP,
  SELECTED PROJECTS, SKILLS, CERTIFICATIONS.
- Real text: the bullet glyph must survive PDF text extraction. The builder
  already patches the bullet font for this - do not replace it with a
  character from a symbol font.
- The contact line is plain text: name, phone, email, LinkedIn, GitHub.
- One page. The ATS reader is a human with a search box; two pages lose the
  second page.

## The one-page budget

Roughly 55 lines of 9.2pt text on A4.

| Section | Lines |
|---|---|
| Header (name, headline, contacts) | 5 |
| Profile | 5 |
| Education | 3 |
| Experience | 8 |
| Leadership | 4 |
| Projects | 5 projects x 5 | 25 |
| Skills | 6 |
| Certifications | 3 |

When it overflows, cut in this order: the weakest project, the second bullet of
each project, the profile, the leadership bullets. Never the font size, never
the eligibility line.
