---
name: design-spec
description: Stage G3. Writes the project's design spec (specs/design-spec.md) from the accepted design or prototype and the client's brand guidelines, computes contrast for every colour pair, and sets the client's values into the canvas app's design tokens (named formulas in App.Formulas). Use when the user runs /design-spec or asks to create the design standards/spec for this project.
disable-model-invocation: true
---

# /design-spec: stage G3

You turn the accepted design and brand guidelines into **values**: tokens, screen anatomy and states.
The mechanics are fixed by `docs/standards/design-standards.md`; read it first, especially §1: **the
client's brand, never Acies'.**

## 0. Before you start

`PROJECT.md` §2: **G2 must be `Approved`.** If G3 is already `Done`, prefer editing the affected
sections and listing what changed over regenerating; run alone, ask first.

## 1. Read

`docs/standards/design-standards.md` · `docs/standards/prototype-fidelity.md` · `docs/templates/design-spec.template.md` ·
`inputs/_converted/SUMMARY.md` · `specs/prototype-fidelity.md` · the original design HTML (its CSS and scripts) if there is one · every design
PNG and PDF page (look at them) · the brand guidelines (text, and the original PDF pages for swatches) ·
the AC dump (`uv run tools/ac_workbook.py dump <workbook>`), for the screen list and the behaviours that
need states · `canvas/<App>/Src/App.pa.yaml` (the current tokens).

## 2. Extract, then decide

1. **Inventory the raw values.** From an HTML prototype, also measure each view **as the browser renders it**: write
   `specs/visual-map.json` (format: `uv run tools/visual_compare.py --help`; sample `samples/design/SAMPLE-visual-map.json`) with
   one entry per screen × state × scheme the prototype shows, each with the CSS selector of the region the screen replaces and
   the `setup` script that opens that view, and the same `scale` as below. Then `uv run tools/visual_compare.py measure <screen>`
   for each: the rendered type (inherited sizes included), colours, radii, padding and shadows. Where it and the CSS reading
   below disagree, the rendered value wins. And: `uv run tools/prototype_design.py inputs/design/<file>.html --content <content width> --out specs/prototype-design.json --formulas`
   (prototype-fidelity §8): tokens for **each scheme**, contrast and compliant shades, type scale in points with label heights,
   radii, spacing, shadows, gradients, fonts. Never pick a value by eye. From images only: sample colours from the PNGs with a script
   (Pillow if installed, or ask), never by eye; measure sizes against the image's width and the app's
   base width. From Figma: `specs/_working/figma/values.md` (`uv run tools/figma_pull.py pull`; type already in points at the
   `scale` in `specs/figma.json`), each value confirmed against the frame's PNG.
2. **Choose the app's base size** (design-standards §6): tablet 1366 × 768 unless the AC or design says
   phone. Record it in the spec's header table.
3. **Cluster into tokens.** Near-duplicates are one token. Map each cluster to a name in
   design-standards §3. Add a name only when none fits, and record it in spec §2 "Added tokens".
4. **No brand guide?** The prototype's CSS (or sampled PNG colours) *is* the brand: tokens come from it,
   cited as "derived from <file>", **in every scheme it defines** (a dark `@media` block means dark tokens too). Keep its
   surfaces as tokens with their alpha (`ColorGlass`, `ColorSegment`, `ColorBackdrop1`...): translucency is built, not dropped. Record that in §10 so the design lead can confirm with the client,
   and note any fonts that aren't in Power Apps' font list (§9).
   **With a brand guide:** reconcile. Where they differ, the design wins (it is what the client
   accepted), but record the difference in §9 and ask in §10 if it looks accidental. A brand font
   Power Apps doesn't offer → the closest offered font, in §3 and §9.
5. **Compute contrast for every text/background and boundary/background pair, in every state.**
   Compute; never estimate:
   ```python
   def lum(h):
       r,g,b=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
       f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
       return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
   def ratio(a,b):
       hi,lo=sorted([lum(a),lum(b)],reverse=True); return (hi+0.05)/(lo+0.05)
   ```
   Text below 4.5:1 (3:1 for large text and control boundaries) gets a **compliant variant**, the
   nearest shade of the same hue that passes. Record it in §8. The design lead tells the client.
6. **Derive** hover/pressed/tint from the primary (mix with white for lighter, black for darker), then
   check each in use.

## 3. Write `specs/design-spec.md`

From the template, every section. Each value cites its source (file + region, or guide page). §1 has
every view in the register's §1. Section 6 describes each screen **as the prototype has it**: its
regions in the prototype's order, each control with its native equivalent (prototype-fidelity §5), the
wording verbatim, the interactions and validations, and the P-IDs it covers. Don't redesign or simplify
there; §9 is the only place a difference goes, with a reason prototype-fidelity §6 allows. Section 6
needs **every screen** with all five states (design-standards §5), including the ones the design doesn't
draw. Mark those "not in design: proposed" so the design lead can find them when reviewing the release
candidate. Unknowns are 🔶 and go in §10.

## 4. Apply the tokens

The **names** of the colour tokens are fixed by `tools/canvas_ui.py` (`TOKENS`, `tokens_block()`): define every one, with the client's values. Sizes are **not** tokens: they are plain numbers measured from the prototype (spec §3–§4, `specs/prototype-design.json`), the `ui-patterns.md` reference numbers only where the prototype gives none (CLAUDE.md D11). Do not invent size tokens or compute layout from them.

Rewrite the token block of `App.Formulas` in `canvas/<App>/Src/App.pa.yaml` with `canvas_ui.tokens_block(overrides, dark=, hexes=)`:
every name from spec §2 as `Name = RGBA(r, g, b, a);`, or `If(IsDark, <dark>, <light>)` when the prototype has a dark scheme, plus
`IsDark` and the `Hex<Name>` texts for SVG images. `App.OnStart` loads `colScheme` from the `ColorScheme` setting (prototype-fidelity §8).
Then `uv run tools/prototype_design.py <file>.html --content <w> --check canvas/<App>/Src/App.pa.yaml`: 0 errors; each warning is a
compliant variant in spec §8. **Keep every existing name** (screens depend
on them), keep the comment line that says tokens live here only, and add a short comment per added
token. YAML rules: the block starts `Formulas: |-` and its first line with `=`; no `: ` inside comments.

Set the app's base size if it changed (`DocumentLayoutWidth`/`Height` are in the `.msapr`; changing them
is a Studio step: put it on the outstanding list and record it in §9 until then).

Then `uv run tools/pp.py build`: 0 errors.

## 5. Finish

- PROJECT.md G3 → `Done`; add §10 questions to PROJECT.md §4.
- Reply with: the palette summary, every accessibility resolution (§8), every deviation (§9), the
  states you had to propose, and open questions.
