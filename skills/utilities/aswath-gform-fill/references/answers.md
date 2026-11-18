# Answers file schema

The answers file is plain JSON. Question keys are the **exact heading text**
shown by `gform.mjs inspect`.

```json
{
  "text": {
    "Name": "Your Name",
    "Register Number": "00000000"
  },
  "radio": {
    "Section": "E",
    "Choose your Specialization": "ECE-Core"
  },
  "grid": {
    "default": ["4", "5", "3", "2", "1"]
  },
  "textDefault": "None"
}
```

| Key | Meaning |
|---|---|
| `text` | Short/long text questions, keyed by heading. Exact match, then prefix match. |
| `radio` | Single-choice questions, keyed by heading. Value is the option text. A prefix match also works (`21ECE221T` matches `21ECE221T - Radar and Navigational Aids`). |
| `grid.default` | Ordered list of rating values. For each grid row the first value in this list that the row offers is used. Rows that are already answered are left alone. |
| `textDefault` | Filled into every text question not listed in `text`. Omit it to leave unlisted text questions empty (they are reported as notes). |

Checkboxes are not scripted: a form that needs them should have their checked
state set by the human in the browser window, then the script fills the rest.

`gform.mjs inspect` writes `gform-inspect.json` listing every page and
question, which is the fastest way to build the answers file.
`assets/answers.template.json` is a valid empty file to copy.
