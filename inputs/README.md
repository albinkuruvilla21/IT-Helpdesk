# inputs/

The client's artefacts, exactly as received. **Never edit a file here.** If a new version arrives, add
it (or replace it) and run `/ingest` again. The tool notices the change, and `/status` shows what it
affects.

| Folder | Put here | Formats | Required |
|---|---|---|---|
| `brd/` | The business requirements document | **.xlsx** (preferred: rows are cited by number), .docx, .pdf | ✅ |
| `transcripts/` | The PO's walkthrough of the features (Teams meeting recording transcript) | **.vtt** (Teams/Stream export), .docx | Optional, but criteria are much better with it |
| `design/` | The **accepted** design or prototype: not drafts. **It is the specification for the app's UI and behaviour** (CLAUDE.md §7), and with no brand guide the source of the colours and fonts. See [The design](#the-design) | **.html** (a working prototype: markup, CSS and scripts) **or the Figma file** (read through its API), plus a **.png** per screen and state | ✅ |
| `branding/` | The client's brand guidelines, logo files | .pdf, .png, .svg | Optional. Without it, colours and fonts are taken from the design |
| `other/` | Anything else the PO points to: existing list exports, a current app's screenshots, process diagrams, sample data | any | |

## The design

The app is built to match the design, and its look is **measured** from it (`tools/prototype_design.py` for HTML,
`tools/figma_pull.py` for Figma; [prototype-fidelity §8](../docs/standards/prototype-fidelity.md)). Images and PDFs
can be inventoried, but not measured: their colours, type and spacing can only be estimated.

| Best | Then | Accepted with a recorded gap |
|---|---|---|
| A working **HTML prototype** (markup, CSS, scripts), with a PNG per screen and state | **The Figma file** itself, read through its API | PNGs or a PDF only: `/ingest` reports a *prototype gap* and records the question |

**If the design is in Figma, use the Figma file itself**: nothing is lost in an export. Put its key and the page holding
the accepted screens in `specs/figma.json` (`{"file": "<key from the URL>", "page": "<page node id>", "scale": <app content
width ÷ frame width>}`), create a Figma personal access token with the read-only *File content* scope, and keep it in
`$FIGMA_TOKEN` or `~/.config/figma/token`, never in the repository (D7). `uv run tools/figma_pull.py pages` lists the
pages and frames; `pull` writes the node tree, a PNG per frame and a values summary (type in points, radii and spacing
scaled to the app) to `specs/_working/figma/`.

**Never accept an HTML made by converting a PDF or an image export**, by hand or by an LLM: it measures the
conversion's mistakes, not the design. An SPFx project that built to one had to redo every web part once the Figma file
was read. If the client can only supply a PDF or images, ask for the Figma file or the prototype's real HTML. Until it
arrives, record it as a question (PROJECT.md §4); `/ingest` reports it as a gap.

**Name files so a citation is meaningful:** `new-request-v2.png`, `2026-10-16-po-walkthrough.vtt`,
`Contoso_SiteRequests_BRD_v2.xlsx`. Criteria cite them by name.

An existing Power Apps app the client wants rebuilt or extended? Put its exported `.msapp` or solution
ZIP in `other/` and say so in `/ingest`: it is read for structure, never copied (it carries the
client's tenant data, PA-T7).

`_converted/` is written by `uv run tools/ingest.py`. Don't edit it either.

Before committing anything here, read [Client documents in the repository](../README.md#client-documents-in-the-repository).
