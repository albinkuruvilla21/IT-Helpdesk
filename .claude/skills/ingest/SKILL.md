---
name: ingest
description: Stage G1. Converts the client artefacts in inputs/ (BRD .xlsx, PO transcript .vtt/.docx, accepted design or prototype .png/.pdf/.html, brand guidelines) into text Claude can read, then reviews and summarises them. Use when the user runs /ingest or has added or changed input files.
disable-model-invocation: true
---

# /ingest: stage G1

## 0. Before you start

Read `PROJECT.md` §2. **G0 must be `Done`.** If not, stop and say: "The project isn't set up yet: run
`/project-setup` first."

## 1. Check what's there

`inputs/README.md` lists the folders. Required: at least one file in `design/`, and either a file in `brd/` or a requirements note in `other/`.
`transcripts/` and `branding/` are optional. If a required folder is empty, stop and say which.

No `branding/`? Carry on **if the design carries the visual values** (an HTML prototype with its CSS, or
PNGs to sample colours from). The brand is then taken from the design, and design-spec records it as
"derived from the prototype, no brand guide". If the design is greyscale or has no usable colours,
add the question to PROJECT.md §4 and carry on with neutral placeholder tokens, marked 🔶.

**A Studio-built reference app.** Is there one (`samples/<app>/`, or a `.msapp` in `inputs/other/`)? If not, say so as a gap and recommend the team builds the main screen in Studio first: a reference proves the layout, and
`docs/standards/ui-patterns.md` requires one or `tools/canvas_ui.py` (see `docs/lessons-learned.md`). Without it, screens are built from the library and Studio will find things; plan a round for that.

**A Figma design.** If the design is a Figma link, or `specs/figma.json` exists, run `uv run tools/figma_pull.py pages`
and `pull` (inputs/README.md *The design*; the token is the user's, never in the repository) and treat the frames'
PNGs and `specs/_working/figma/values.md` as the design. A design HTML that was converted from a PDF or images is not a
design: say so and ask for the source.

Run `uv run tools/ingest.py --status` and report anything new or changed.

## 2. Convert

`uv run tools/ingest.py`. If it prints **PROTOTYPE GAP**, add the question it names to PROJECT.md §4 (ask for the
Figma file or the prototype's HTML; baseline: the look is estimated from the images and marked 🔶 in the design spec)
and list it under *Gaps* in `SUMMARY.md`. On a failure, report the file and the error. If `markitdown` can't read a
file, ask the user for a different export (e.g. a PDF saved as .docx). Don't skip it silently.

## 3. Review every converted input

Open each one. You are checking that it is **usable**, not drafting requirements yet.

| Input | Check |
|---|---|
| BRD (`_converted/brd/*.md`) | Every sheet came through; note sheet names, row counts, which sheets hold requirements vs. reference data; flag merged-cell damage or empty sheets |
| Transcript | Speakers identified; rough duration; any stretch that is garbled |
| Design HTML | **Read the original `.html`** (and any CSS and JS beside it), not only the converted copy: every view, including the ones a click reveals, and every control, validation, message, action and state (§3a). Its scripted behaviour is the specification: the app rebuilds it in Power Fx. If a browser tool is available, open it and screenshot each view and state into the scratchpad |
| Design PNGs | **Look at every image.** List what each one shows: screen, state (empty, error, filled), and the controls you can see (lists, forms, dropdowns, date pickers). Note controls a canvas app can't do as drawn (hover menus, drag-and-drop) |
| Design PDFs | The text extract loses layout, so **render every page and look at it**. The Read tool needs poppler, which is often missing; `pypdfium2` (installed with markitdown's PDF support) renders to PNG in the scratchpad. A PDF that fails to open is usually a truncated upload (no `%%EOF`): ask for a new export, don't skip it. Fonts are rarely embedded, so say so |
| Accepted? | The inputs README wants the **accepted** design. Record which design, which version and when the client accepted it. If nothing says, add a question: every later "as shown in the design" depends on it |
| Secrets | Search every converted input for passwords, tokens, keys and logins (BRD trackers often carry a *Credentials* sheet). If found: say so first, never copy them into any document, and warn that `inputs/` and `inputs/_converted/` are committed by default. Check `git ls-files inputs` before claiming anything is or isn't in history |
| Brand guidelines | Colour values, fonts, logo rules present in text? If colours are only in swatches, open the original PDF pages and read them. Note whether the brand font is one Power Apps offers |
| An existing app or solution in `other/` | List its screens, data sources and flows for the summary. **Never copy it**: it carries the client's tenant URLs, people and connections (PA-T7). Run `uv run tools/pp.py validate --no-roundtrip <zip>` on a solution ZIP and summarise what it finds |

## 3a. Inventory the prototype

The accepted prototype is the specification for the UI (CLAUDE.md §7). Read
`docs/standards/prototype-fidelity.md` §3, then write `specs/prototype-fidelity.md` from
`docs/templates/prototype-fidelity.template.md`:

- §1: every view, how it is reached, the screen or dialog it will become.
- §2: one `P-nn` row per element or behaviour, using §3's table as the checklist: regions in order,
  every control (type, label, placeholder, default, options in order), every validation (rule, when it
  fires, **exact message**), every action and its result, navigation, conditional display, list
  columns, sorting and filters, derived values, states, roles, responsive changes. Wording verbatim.
  Prototype reference = file + selector or function name (`prototype.html #frmNew`, `validate()`).
  Status `Not built`; AC IDs empty (G2 fills them).
- Mock data in the prototype's scripts: note its fields in SUMMARY.md, as the first draft of the data
  model.
- **The look** (prototype-fidelity §8): `uv run tools/prototype_design.py inputs/design/<file>.html --content 1020 --out specs/prototype-design.json`
  (1020 is the default content width at the 1366 base; use the project's). Add `style` rows for the schemes, background, chrome,
  cards, buttons, badges, fields and type scale, and put the report's schemes, fonts and failing contrast pairs in SUMMARY.md.

Go through the source twice: once by view, once by script function, so behaviour wired from a script
isn't missed. Behaviour you can't determine (an image-only prototype, a handler that does nothing) is
an open question with a baseline. **On a re-ingest** with a changed prototype: re-inventory the changed
views, keep existing P-IDs and statuses, add rows, and mark rows whose element is gone `Out of scope`
with a note, never delete them.

## 3b. Suggest what to reuse

Do `/catalogue suggest` (`.claude/skills/catalogue/SKILL.md` §2) against the features the BRD and the prototype
show. Add a **Reuse candidates** section to `SUMMARY.md` (feature → catalogue entry, and why it fits) and
the matches to PROJECT.md §8 as *Suggested*. If the catalogue can't be reached, say so in `SUMMARY.md`
and carry on: `/build-plan` checks it again. An empty catalogue is not a failure.

## 4. Write `inputs/_converted/SUMMARY.md`

For the BA and the next stage: one section per input with the findings above, then **Gaps**: things later
stages will need and the inputs don't contain (no transcript, no brand guide, then say which, and what
the later stages will do instead; e.g. "no hover states in the design", "brand guide has
no web font"). Add each gap that needs a client answer to PROJECT.md §4 as an open question.

## 5. Finish

- G1 Status → `Done`.
- **Commit the inputs**, originals and `_converted/` together, with `specs/prototype-fidelity.md` and PROJECT.md:
  `G1: inputs` (a re-ingest: `G1: inputs — <what changed>`). Other developers clone them instead of collecting
  them again. Don't commit, and say why, if:
  - the secrets check found anything (the client must send a clean copy, or the user removes it first);
  - PROJECT.md §3 records that this client's documents stay off GitHub (README *Client documents in the
    repository*);
  - a file is over 50 MB (GitHub refuses 100 MB). Ask for a smaller export, or keep it on the project's
    SharePoint site and put its link in `inputs/other/links.md`;
  - an existing app or solution in `other/` has not been reviewed: it carries tenant URLs, people and
    connection IDs (PA-T7).
- Reply: what was converted, the prototype inventory (views, number of register rows by kind), the
  gaps, the reuse candidates, and the next step: `/acceptance-criteria`.
- If this was a **re-ingest** and inputs changed, say which `Done` stages (and the G2 sign-off) may be
  affected and suggest `/status`.
